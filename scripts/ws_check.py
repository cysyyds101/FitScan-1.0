import asyncio
import websockets
import json

async def check():
    try:
        async with websockets.connect('ws://localhost:8765', open_timeout=5) as ws:
            header_raw = await asyncio.wait_for(ws.recv(), timeout=5)
            header = json.loads(header_raw)
            simulated = header.get('simulated', 'unknown')
            mode = 'SIMULATED' if simulated else 'REALSENSE SR300'
            print(f'[capture] Mode: {mode}')
            print(f'[capture] FPS: {header.get("fps")}, Resolution: {header.get("width")}x{header.get("height")}')
            m = header.get('body_measurements', {})
            print(f'[capture] Measurements: height={m.get("height_cm")}cm, shoulder={m.get("shoulder_width_cm")}cm, arm={m.get("arm_length_cm")}cm')
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(check())
