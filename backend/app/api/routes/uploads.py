"""Uploads API.

- POST /api/uploads                     multipart file -> 201 {id, url, ...}
- GET  /api/uploads/{id}                get one
- GET  /api/uploads                     list recent (limit=20)
- POST /api/uploads/{id}/normalize      enqueue normalize on AI server
- PATCH /api/uploads/{id}/normalized    AI server callback with result
- GET  /api/uploads/{id}/normalized     poll normalize status

The router does no business logic — all writes go through
services.upload_storage or services.normalize_service.
"""
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.api.schemas import NormalizeUpdate, UploadItem
from app.services import normalize_service, upload_storage

router = APIRouter()


@router.post("/uploads", response_model=UploadItem, status_code=201)
async def create_upload(
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
):
    """Accept a multipart image upload. Persists to disk + DB."""
    if not file.content_type:
        raise HTTPException(status_code=400, detail="missing content-type")

    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"read failed: {e}")

    try:
        upload_id, abs_path, size = upload_storage.save_file_to_disk(
            file_bytes=file_bytes,
            mime=file.content_type,
            original_filename=file.filename,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return upload_storage.insert_upload(
        upload_id=upload_id,
        abs_path=abs_path,
        mime=file.content_type,
        size=size,
        user_id=user_id,
    )


@router.get("/uploads/{upload_id}", response_model=UploadItem)
def get_upload(upload_id: str):
    item = upload_storage.get_upload(upload_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"upload '{upload_id}' not found")
    return item


@router.get("/uploads", response_model=list[UploadItem])
def list_uploads(limit: int = 20):
    return upload_storage.list_uploads(limit=limit)


# ─── Phase C: normalize ─────────────────────────────────────────────────────

@router.post("/uploads/{upload_id}/normalize", response_model=UploadItem, status_code=202)
def trigger_normalize(upload_id: str, request: Request):
    """Mark upload as QUEUED and enqueue normalize on AI server.

    Phase C rule: UPLOAD ≠ PROCESSING. The upload is already on disk;
    this endpoint is what kicks off the AI server's PIL crop.

    The AI server will PATCH /api/uploads/{id}/normalized when done.
    """
    # Build the callback URL the AI server should PATCH. We use the
    # request's host so this works behind reverse proxies in prod.
    base = str(request.base_url).rstrip("/")
    callback = f"{base}/api/uploads/{upload_id}/normalized"

    try:
        ai_resp = normalize_service.trigger_normalize(
            upload_id=upload_id,
            backend_callback_url=callback,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    if not ai_resp or ai_resp.get("status") == "ERROR" or not ai_resp.get("task_id"):
        # AI server unreachable: keep row at QUEUED so caller knows
        raise HTTPException(
            status_code=502,
            detail=f"AI server normalize enqueue failed: {ai_resp}",
        )

    # Store the AI server task_id so frontend can correlate / poll
    from app.services import storage as _storage
    conn = _storage.get_db()
    conn.execute(
        "UPDATE uploads SET normalize_task_id = ? WHERE id = ?",
        (ai_resp["task_id"], upload_id),
    )
    conn.commit()
    return upload_storage.get_upload(upload_id)


@router.patch("/uploads/{upload_id}/normalized", response_model=UploadItem)
def patch_normalized(upload_id: str, body: NormalizeUpdate):
    """AI server PATCHes this with the result of the normalize worker.

    The AI server is authenticated only by reachability in dev — prod
    should add a shared-secret header.
    """
    if upload_storage.get_upload(upload_id) is None:
        raise HTTPException(status_code=404, detail=f"upload '{upload_id}' not found")
    try:
        return normalize_service.set_normalize_result(
            upload_id=upload_id,
            status=body.status,
            normalized_path=body.normalized_path,
            task_id=body.task_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/uploads/{upload_id}/normalized", response_model=UploadItem)
def get_normalized(upload_id: str):
    """Poll endpoint: returns the upload row including normalize fields."""
    item = upload_storage.get_upload(upload_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"upload '{upload_id}' not found")
    return item
