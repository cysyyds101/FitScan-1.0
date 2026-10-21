#!/usr/bin/env bash
# setup_mirror_env.sh — bootstrap the local real-time mirror environment on Windows.
#
# Why this script exists (all of these cost real debugging time to rediscover):
#
# 1. `python` on PATH is C:\Espressif\tools\python\python.exe (the ESP-IDF
#    toolchain). It has none of this project's dependencies. Do not use it.
# 2. `conda` and `pip` are not on PATH. Anaconda lives at
#    C:\Users\user\anaconda3 but is only reachable by absolute path.
# 3. The conda env `torch_gpu` already has torch 2.11.0+cu128 built with
#    sm_120, which is what the RTX 5070 (Blackwell) needs. Reinstalling torch
#    elsewhere is a 3GB download and risks losing cu128 support.
# 4. pip MUST get --only-binary=:all:. `uvicorn[standard]` pulls httptools and
#    uvloop, which have no cp310 win_amd64 wheels — pip silently falls back to a
#    source build and hangs with no output. This looks like a slow network but is
#    not. Use plain `uvicorn` instead of the [standard] extra.
#
# Usage:  bash scripts/setup_mirror_env.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_PY="/c/Users/user/anaconda3/envs/torch_gpu/python.exe"
VENV="$REPO/.venv"

if [ ! -x "$BASE_PY" ]; then
  echo "FATAL: $BASE_PY not found." >&2
  echo "       The mirror env is built on conda env 'torch_gpu' for its torch+cu128." >&2
  echo "       Recreate that env with a torch built for cu128/sm_120 first." >&2
  exit 1
fi

if [ ! -d "$VENV/Scripts" ]; then
  echo ">>> creating $VENV (inherits torch_gpu site-packages)"
  "$BASE_PY" -m venv --system-site-packages "$VENV"
fi

PY="$VENV/Scripts/python.exe"

echo ">>> installing backend/mirror/requirements.txt (binary wheels only)"
"$PY" -m pip install --only-binary=:all: --progress-bar off \
  -r "$REPO/backend/mirror/requirements.txt"

echo ">>> verifying"
"$PY" - <<'EOF'
import importlib
required = ["pyrealsense2", "cv2", "fastapi", "uvicorn", "websockets",
            "httpx", "pydantic", "numpy", "torch", "PIL"]
missing = []
for m in required:
    try:
        mod = importlib.import_module(m)
        print(f"  OK   {m:<13} {getattr(mod, '__version__', '?')}")
    except Exception:
        missing.append(m)
        print(f"  MISS {m}")

import torch
ok_cuda = torch.cuda.is_available()
print(f"\n  CUDA available : {ok_cuda}")
if ok_cuda:
    print(f"  device         : {torch.cuda.get_device_name(0)}")
    print(f"  sm_120 support : {'sm_120' in torch.cuda.get_arch_list()}")

if missing or not ok_cuda:
    raise SystemExit(1)
print("\n[OK] mirror environment ready")
EOF

echo
echo ">>> SP-1 regression (Phase A queue pipeline must still pass)"
(cd "$REPO" && "$PY" tests/sp1_smoke.py) | tail -3

echo
echo "Next: plug in the SR300, then run the capture diagnostics."
