/**
 * HumanModel.jsx — 人体模型。
 *
 * 规则（Virtual Try-On Rule）：
 *  - 只负责人体本身，不含任何服装逻辑
 *  - 自动居中、自动缩放到 ~1.8m
 *  - 加载失败/缺失时回退到程序化胶囊人体
 *  - 通过 onMount 回调把根 group ref 暴露给父级，让 ClothingOverlay 挂载到同一根
 */
import { useGLTF } from '@react-three/drei';
import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { isValidGLB } from '../core/GLBLoader';

const HUMAN_URL = '/models/human.glb';

/**
 * 程序化人体（回退方案）。
 * 用 capsule + sphere 拼出一个"看得过去的"人形剪影。
 */
function ProceduralHuman({ onMount }) {
  const groupRef = useRef();

  useEffect(() => {
    if (groupRef.current && onMount) onMount(groupRef.current);
  }, [onMount]);

  return (
    <group ref={groupRef} dispose={null}>
      <mesh position={[0, 1.7, 0]} castShadow>
        <sphereGeometry args={[0.13, 32, 32]} />
        <meshStandardMaterial color="#e9c4a0" roughness={0.6} />
      </mesh>
      <mesh position={[0, 1.55, 0]} castShadow>
        <cylinderGeometry args={[0.06, 0.07, 0.08, 16]} />
        <meshStandardMaterial color="#e9c4a0" roughness={0.6} />
      </mesh>
      <mesh position={[0, 1.1, 0]} castShadow>
        <capsuleGeometry args={[0.22, 0.7, 8, 16]} />
        <meshStandardMaterial color="#3a4a5e" roughness={0.7} />
      </mesh>
      <mesh position={[0, 0.7, 0]} castShadow>
        <capsuleGeometry args={[0.2, 0.2, 8, 16]} />
        <meshStandardMaterial color="#2a3a4e" roughness={0.7} />
      </mesh>
      <mesh position={[-0.3, 1.2, 0]} rotation={[0, 0, 0.12]} castShadow>
        <capsuleGeometry args={[0.07, 0.55, 6, 12]} />
        <meshStandardMaterial color="#e9c4a0" roughness={0.6} />
      </mesh>
      <mesh position={[0.3, 1.2, 0]} rotation={[0, 0, -0.12]} castShadow>
        <capsuleGeometry args={[0.07, 0.55, 6, 12]} />
        <meshStandardMaterial color="#e9c4a0" roughness={0.6} />
      </mesh>
      <mesh position={[-0.1, 0.32, 0]} castShadow>
        <capsuleGeometry args={[0.09, 0.7, 6, 12]} />
        <meshStandardMaterial color="#1f2a3a" roughness={0.7} />
      </mesh>
      <mesh position={[0.1, 0.32, 0]} castShadow>
        <capsuleGeometry args={[0.09, 0.7, 6, 12]} />
        <meshStandardMaterial color="#1f2a3a" roughness={0.7} />
      </mesh>
    </group>
  );
}

/**
 * 真实 GLB 人体（带自动居中 + 自动缩放）。
 */
function GLBHuman({ url, onMount }) {
  const gltf = useGLTF(url, true, true);
  const ref = useRef();
  const [box] = useState(() => new THREE.Box3());

  useEffect(() => {
    if (!ref.current || !gltf?.scene) return;

    const obj = gltf.scene;
    obj.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });

    box.setFromObject(obj);
    const size = new THREE.Vector3();
    box.getSize(size);
    const center = new THREE.Vector3();
    box.getCenter(center);

    obj.position.x -= center.x;
    obj.position.z -= center.z;

    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const targetHeight = 1.8;
    const s = targetHeight / maxDim;
    obj.scale.setScalar(s);

    obj.position.y = -box.min.y * s;

    ref.current.add(obj);
    if (onMount) onMount(ref.current);

    return () => {
      ref.current?.remove(obj);
    };
  }, [gltf, onMount, box]);

  return <group ref={ref} />;
}

export default function HumanModel({ onMount, position = [0, 0, 0] }) {
  // 默认用 procedural，避免坏 GLB 先喂给 useGLTF 抛 "is not valid JSON"
  const [useFallback, setUseFallback] = useState(true);

  useEffect(() => {
    let alive = true;
    isValidGLB(HUMAN_URL).then((ok) => {
      if (alive && ok) setUseFallback(false);
    });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <group position={position}>
      {useFallback ? (
        <ProceduralHuman onMount={onMount} />
      ) : (
        <GLBHuman url={HUMAN_URL} onMount={onMount} />
      )}
    </group>
  );
}

useGLTF.preload(HUMAN_URL);
