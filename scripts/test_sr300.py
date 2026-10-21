import pyrealsense2 as rs
pipe = rs.pipeline()
cfg = rs.config()
cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
pipe.start(cfg)
for i in range(5):
    frames = pipe.wait_for_frames(timeout_ms=3000)
    depth = frames.get_depth_frame()
    print(f'Frame {i}: valid={depth.is_depth_frame()}')
pipe.stop()
print('done')
