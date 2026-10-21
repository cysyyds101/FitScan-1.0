/**
 * Scene.jsx — 整个应用唯一的三维场景容器。
 *
 * 规则（Frontend Rule #2）：
 *  - 全局只允许一个 <Canvas>
 *  - Camera / Light 由这里集中管理
 *  - 子组件只挂载 Object3D，不允许自己 new Renderer / Scene
 */
import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei';

const CAMERA = { position: [0, 1.4, 3.2], fov: 45 };
const LIGHTS = {
  ambient: { intensity: 0.55 },
  key: { position: [3, 4, 2], intensity: 1.1 },
  rim: { position: [-3, 2, -2], intensity: 0.4 },
};

export default function Scene({ children }) {
  return (
    <Canvas
      camera={CAMERA}
      shadows
      dpr={[1, 2]}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      style={{ width: '100%', height: '100%', background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)' }}
    >
      <ambientLight intensity={LIGHTS.ambient.intensity} />
      <directionalLight
        position={LIGHTS.key.position}
        intensity={LIGHTS.key.intensity}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <directionalLight position={LIGHTS.rim.position} intensity={LIGHTS.rim.intensity} />

      <Suspense fallback={null}>{children}</Suspense>

      <ContactShadows position={[0, 0, 0]} opacity={0.4} scale={6} blur={2.4} far={2} />
      <OrbitControls
        target={[0, 1, 0]}
        enablePan={false}
        minDistance={1.5}
        maxDistance={6}
        minPolarAngle={Math.PI * 0.15}
        maxPolarAngle={Math.PI * 0.55}
      />
    </Canvas>
  );
}
