"""Clothing API routes。

- GET  /api/clothing           列表
- GET  /api/clothing/{id}      详情
- POST /api/clothing/upload    H1: 用户上传 GLB（multipart）
"""
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.schemas import ClothingItem, ClothingListResponse
from app.services import storage

router = APIRouter()

# H1: hard limits — keep upload DoS-safe even in dev.
MAX_GLB_BYTES = 10 * 1024 * 1024  # 10 MB — matches SPEC §6 perf budget
ALLOWED_CATEGORIES = {"top", "bottom", "outer", "full", "accessory"}


@router.get("/clothing", response_model=ClothingListResponse)
def list_clothing():
    items = storage.list_clothing()
    return ClothingListResponse(items=items, total=len(items))


@router.get("/clothing/{item_id}", response_model=ClothingItem)
def get_clothing(item_id: str):
    item = storage.get_clothing(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"clothing '{item_id}' not found")
    return item


@router.post("/clothing/upload", response_model=ClothingItem, status_code=201)
async def upload_clothing(
    file: UploadFile = File(..., description="GLB binary"),
    name: str | None = Form(None),
    category: str = Form("top"),
    description: str = Form(""),
):
    """H1: accept a user-uploaded GLB and register it as a clothing item.

    Validation:
      - filename suffix must be .glb (browser-side check too, but enforce here)
      - size <= 10 MB
      - category must be in ALLOWED_CATEGORIES (else 422)
    """
    # 1. filename / mime sanity
    fname = (file.filename or "").lower()
    if not fname.endswith(".glb"):
        raise HTTPException(status_code=400, detail="Only .glb files are supported")
    if file.content_type and file.content_type not in ("model/gltf-binary", "application/octet-stream"):
        # Some browsers send application/octet-stream — accept it. Anything else: 415.
        raise HTTPException(status_code=415, detail=f"Unsupported content-type: {file.content_type}")

    # 2. category
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"category must be one of {sorted(ALLOWED_CATEGORIES)}",
        )

    # 3. read body with size guard
    blob = await file.read()
    if len(blob) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(blob) > MAX_GLB_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(blob)} bytes); max {MAX_GLB_BYTES}",
        )

    # 4. magic-byte sniff — GLB starts with 'glTF' (0x67 0x6C 0x54 0x46)
    if blob[:4] != b"glTF":
        raise HTTPException(
            status_code=400,
            detail="Not a valid GLB file (missing glTF magic header)",
        )

    # 5. derive a friendly name from the filename if the user didn't provide one
    final_name = (name or "").strip() or fname.rsplit("/", 1)[-1].rsplit(".", 1)[0]

    item = storage.create_uploaded_clothing(
        name=final_name,
        glb_bytes=blob,
        category=category,
        description=description,
    )
    return item
