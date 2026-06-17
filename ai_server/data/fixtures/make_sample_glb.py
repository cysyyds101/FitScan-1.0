"""Generate a minimal valid GLB fixture for SP-4 testing.

Hand-builds a 1-triangle GLB so we can verify the pipeline (worker writes
GLB -> backend serves via /static/reconstructions/) without any 3D libs.

GLB layout (glTF 2.0 spec):
    [12B header][8B JSON chunk header][JSON][8B BIN chunk header][BIN]
    padded to 4-byte alignment.

We never load this with a renderer in tests; we just assert the magic,
version, and total length to confirm it round-tripped.
"""
import json
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
# .../ai_server/data/fixtures/make_sample_glb.py  ->  .../ai_server/data/fixtures/sample.glb
OUT = os.path.join(HERE, "sample.glb")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

json_chunk = json.dumps({
    "asset": {"version": "2.0", "generator": "fitscan-test-fixture"},
    "scene": 0,
    "scenes": [{"nodes": [0]}],
    "nodes":  [{"mesh": 0}],
    "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "mode": 4}]}],
    "accessors": [
        {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
         "max": [1.0, 1.0, 0.0], "min": [0.0, 0.0, 0.0]},
        {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
    ],
    "bufferViews": [
        {"buffer": 0, "byteOffset": 0,  "byteLength": 36},
        {"buffer": 0, "byteOffset": 36, "byteLength": 6},
    ],
    "buffers": [{"byteLength": 42}],
}).encode("utf-8")

# Pad to 4-byte alignment with spaces
while len(json_chunk) % 4 != 0:
    json_chunk += b" "

# One triangle: (0,0,0) (1,0,0) (0,1,0)
positions = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
indices = struct.pack("<3H", 0, 1, 2)
bin_chunk = positions + indices
while len(bin_chunk) % 4 != 0:
    bin_chunk += b"\x00"

json_header = struct.pack("<II", len(json_chunk), 0x4E4F534A)  # "JSON"
bin_header = struct.pack("<II", len(bin_chunk), 0x004E4942)   # "BIN\0"
total_len = 12 + 8 + len(json_chunk) + 8 + len(bin_chunk)
glb_header = struct.pack("<4sII", b"glTF", 2, total_len)

glb = glb_header + json_header + json_chunk + bin_header + bin_chunk

with open(OUT, "wb") as f:
    f.write(glb)

print(f"wrote {len(glb)} bytes to {OUT}")
print(f"  magic={glb[:4]!r}  version={struct.unpack('<I', glb[4:8])[0]}  total={total_len}")
print(f"  json_chunk={len(json_chunk)}B  bin_chunk={len(bin_chunk)}B")
