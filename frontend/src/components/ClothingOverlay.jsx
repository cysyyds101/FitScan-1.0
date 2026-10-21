/**
 * ClothingOverlay.jsx — 服装叠加层。
 *
 * 绑定方式（Virtual Try-On Rule #1 优先级）：
 *  1. group transform（平移/缩放/旋转）—— 主绑定
 *  2. vertex offset 伪布料 —— 委托给 ClothPhysics 子组件
 *
 * 行为：
 *  - 接收父级传入的 transform（position/rotation/scale）
 *  - 优先加载 GLB；缺失时回退到程序化几何服装
 *  - 把 useFrame 内的顶点位移逻辑抽到 ClothPhysics，保持本组件"只挂 mesh + transform"
 */
import { useGLTF } from '@react-three/drei';
import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import ClothPhysics from './ClothPhysics';
import { isValidGLB } from '../core/GLBLoader';

const TINT = {
  c01: '#2563eb',
  c02: '#dc2626',
  c03: '#16a34a',
};

/**
 * 程序化服装几何（回退方案）。薄壳 cylinder + torus 模拟贴身衣服。
 */
function ProceduralClothing({ id }) {
  const groupRef = useRef();
  const color = TINT[id] ?? '#94a3b8';

  return (
    <group ref={groupRef}>
      <mesh position={[0, 1.15, 0]} castShadow>
        <cylinderGeometry args={[0.235, 0.21, 0.7, 32, 1, true]} />
        <meshStandardMaterial color={color} roughness={0.55} metalness={0.05} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0, 1.5, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.09, 0.018, 12, 32]} />
        <meshStandardMaterial color={color} roughness={0.6} />
      </mesh>
      <mesh position={[-0.31, 1.25, 0]} rotation={[0, 0, 0.12]} castShadow>
        <cylinderGeometry args={[0.075, 0.06, 0.45, 24, 1, true]} />
        <meshStandardMaterial color={color} roughness={0.6} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0.31, 1.25, 0]} rotation={[0, 0, -0.12]} castShadow>
        <cylinderGeometry args={[0.075, 0.06, 0.45, 24, 1, true]} />
        <meshStandardMaterial color={color} roughness={0.6} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

/**
 * 真实 GLB 服装（带 group transform）。
 */
function GLBClothing({ url, transform }) {
  const gltf = useGLTF(url, true, true);
  const groupRef = useRef();

  useEffect(() => {
    if (!gltf?.scene || !groupRef.current) return;
    gltf.scene.traverse((c) => {
      if (c.isMesh) {
        c.castShadow = true;
        c.receiveShadow = true;
      }
    });
    groupRef.current.add(gltf.scene);
    return () => {
      groupRef.current?.remove(gltf.scene);
    };
  }, [gltf]);

  return (
    <group
      ref={groupRef}
      position={transform.position ?? [0, 0, 0]}
      rotation={transform.rotation ?? [0, 0, 0]}
      scale={transform.scale ?? [1, 1, 1]}
    />
  );
}

function useFallbackState(url) {
  // 默认 fallback=true：坏 GLB 不会先进 useGLTF
  const [fb, setFb] = useState(true);
  useEffect(() => {
    if (!url) {
      setFb(true);
      return;
    }
    let alive = true;
    isValidGLB(url).then((ok) => {
      if (alive) setFb(!ok);
    });
    return () => {
      alive = false;
    };
  }, [url]);
  return [fb, setFb];
}

/**
 * ClothingOverlay — 把"挂 mesh + transform"和"伪布料动画"两层分离。
 * 内部用 ClothPhysics 子组件实现 vertex offset 呼吸效果。
 */
export default function ClothingOverlay({ clothing, transform, vertexOffset }) {
  const url = clothing?.model_url;
  const id = clothing?.id ?? 'unknown';
  const [useFallback] = useFallbackState(url);

  return (
    <ClothPhysics enabled={vertexOffset} baseY={transform.position?.[1] ?? 0}>
      {useFallback || !url ? (
        <group
          position={transform.position ?? [0, 0, 0]}
          rotation={transform.rotation ?? [0, 0, 0]}
          scale={transform.scale ?? [1, 1, 1]}
        >
          <ProceduralClothing id={id} />
        </group>
      ) : (
        <GLBClothing url={url} transform={transform} />
      )}
    </ClothPhysics>
  );
}
