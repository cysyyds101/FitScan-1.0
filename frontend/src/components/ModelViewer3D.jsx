/**
 * FitScan 3D 场景组件
 * 使用 Three.js 实现 3D 人体模型可视化
 */
import React, { useRef, useState, useEffect, Suspense } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Environment, useTexture, Html, Float } from '@react-three/drei'
import * as THREE from 'three'

// 人体模型组件
function BodyModel({ measurements, onHover, onClick, highlighted }) {
  const meshRef = useRef()

  // 基础尺寸（默认170cm身高）
  const scale = measurements?.height ? measurements.height / 170 : 1

  useFrame(() => {
    if (meshRef.current) {
      // 轻微浮动动画
      meshRef.current.position.y = Math.sin(Date.now() * 0.001) * 0.05
    }
  })

  return (
    <group ref={meshRef} scale={scale}>
      {/* 头部 */}
      <mesh position={[0, 1.6, 0]} onPointerOver={onHover} onClick={onClick}>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial
          color={highlighted ? '#4CAF50' : '#E0E0E0'}
          roughness={0.4}
        />
      </mesh>

      {/* 颈部 */}
      <mesh position={[0, 1.4, 0]} onPointerOver={onHover} onClick={onClick}>
        <cylinderGeometry args={[0.04, 0.05, 0.15, 16]} />
        <meshStandardMaterial color="#E0E0E0" roughness={0.4} />
      </mesh>

      {/* 躯干 */}
      <mesh position={[0, 1.1, 0]} onPointerOver={onHover} onClick={onClick}>
        <boxGeometry args={[0.35, 0.5, 0.18]} />
        <meshStandardMaterial
          color={highlighted ? '#4CAF50' : '#2196F3'}
          roughness={0.3}
          metalness={0.1}
          transparent
          opacity={0.8}
        />
      </mesh>

      {/* 左肩 */}
      <mesh position={[-0.22, 1.3, 0]} onPointerOver={onHover} onClick={onClick}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color="#E0E0E0" roughness={0.4} />
      </mesh>

      {/* 右肩 */}
      <mesh position={[0.22, 1.3, 0]} onPointerOver={onHover} onClick={onClick}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color="#E0E0E0" roughness={0.4} />
      </mesh>

      {/* 左臂 */}
      <mesh position={[-0.28, 1.0, 0]} rotation={[0, 0, 0.1]} onPointerOver={onHover} onClick={onClick}>
        <cylinderGeometry args={[0.04, 0.035, 0.4, 16]} />
        <meshStandardMaterial color="#E0E0E0" roughness={0.4} />
      </mesh>

      {/* 右臂 */}
      <mesh position={[0.28, 1.0, 0]} rotation={[0, 0, -0.1]} onPointerOver={onHover} onClick={onClick}>
        <cylinderGeometry args={[0.04, 0.035, 0.4, 16]} />
        <meshStandardMaterial color="#E0E0E0" roughness={0.4} />
      </mesh>

      {/* 左手 */}
      <mesh position={[-0.3, 0.78, 0]} onPointerOver={onHover} onClick={onClick}>
        <sphereGeometry args={[0.05, 16, 16]} />
        <meshStandardMaterial color="#E0E0E0" roughness={0.4} />
      </mesh>

      {/* 右手 */}
      <mesh position={[0.3, 0.78, 0]} onPointerOver={onHover} onClick={onClick}>
        <sphereGeometry args={[0.05, 16, 16]} />
        <meshStandardMaterial color="#E0E0E0" roughness={0.4} />
      </mesh>

      {/* 腰部 */}
      <mesh position={[0, 0.82, 0]} onPointerOver={onHover} onClick={onClick}>
        <cylinderGeometry args={[0.14, 0.12, 0.15, 16]} />
        <meshStandardMaterial color="#2196F3" roughness={0.3} />
      </mesh>

      {/* 左腿 */}
      <mesh position={[-0.1, 0.45, 0]} onPointerOver={onHover} onClick={onClick}>
        <cylinderGeometry args={[0.07, 0.06, 0.55, 16]} />
        <meshStandardMaterial color="#1565C0" roughness={0.3} />
      </mesh>

      {/* 右腿 */}
      <mesh position={[0.1, 0.45, 0]} onPointerOver={onHover} onClick={onClick}>
        <cylinderGeometry args={[0.07, 0.06, 0.55, 16]} />
        <meshStandardMaterial color="#1565C0" roughness={0.3} />
      </mesh>

      {/* 左脚 */}
      <mesh position={[-0.1, 0.12, 0.05]} onPointerOver={onHover} onClick={onClick}>
        <boxGeometry args={[0.08, 0.05, 0.15]} />
        <meshStandardMaterial color="#E0E0E0" roughness={0.4} />
      </mesh>

      {/* 右脚 */}
      <mesh position={[0.1, 0.12, 0.05]} onPointerOver={onHover} onClick={onClick}>
        <boxGeometry args={[0.08, 0.05, 0.15]} />
        <meshStandardMaterial color="#E0E0E0" roughness={0.4} />
      </mesh>

      {/* 测量数据标签 */}
      {measurements && (
        <>
          <Html position={[0, 1.6, 0.2]} style={{ color: 'white', fontSize: '10px' }}>
            <div style={{ background: 'rgba(0,0,0,0.6)', padding: '2px 6px', borderRadius: '4px' }}>
              身高: {measurements.height?.toFixed(1)}cm
            </div>
          </Html>
        </>
      )}
    </group>
  )
}

// 地面网格
function Ground() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
      <planeGeometry args={[10, 10]} />
      <meshStandardMaterial color="#1a1a2e" />
    </mesh>
  )
}

// 环形光效
function RingLights() {
  const ringRef = useRef()

  useFrame(({ clock }) => {
    if (ringRef.current) {
      ringRef.current.rotation.z = clock.getElapsedTime() * 0.2
    }
  })

  return (
    <group ref={ringRef}>
      <mesh position={[0, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.5, 0.02, 16, 100]} />
        <meshBasicMaterial color="#00ffff" transparent opacity={0.3} />
      </mesh>
      <mesh position={[0, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.8, 0.02, 16, 100]} />
        <meshBasicMaterial color="#ff00ff" transparent opacity={0.2} />
      </mesh>
    </group>
  )
}

// 粒子效果
function Particles() {
  const particlesRef = useRef()
  const count = 200

  const positions = new Float32Array(count * 3)
  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 10
    positions[i * 3 + 1] = Math.random() * 5
    positions[i * 3 + 2] = (Math.random() - 0.5) * 10
  }

  useFrame(({ clock }) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y = clock.getElapsedTime() * 0.05
    }
  })

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.02} color="#00ffff" transparent opacity={0.6} />
    </points>
  )
}

// 3D 场景主组件
function Scene({ measurements, onPartClick }) {
  const [hoveredPart, setHoveredPart] = useState(null)

  return (
    <>
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, 5, -10]} intensity={0.5} color="#ff00ff" />
      <spotLight
        position={[0, 10, 0]}
        angle={0.3}
        penumbra={1}
        intensity={1}
        castShadow
      />

      <Suspense fallback={null}>
        <BodyModel
          measurements={measurements}
          highlighted={hoveredPart !== null}
          onHover={() => setHoveredPart('body')}
          onClick={() => onPartClick?.('body')}
        />
        <Environment preset="city" />
      </Suspense>

      <Ground />
      <RingLights />
      <Particles />

      <OrbitControls
        enablePan={false}
        enableZoom={true}
        minDistance={2}
        maxDistance={8}
        minPolarAngle={Math.PI / 4}
        maxPolarAngle={Math.PI / 1.5}
      />
    </>
  )
}

// 主导出组件
export default function ModelViewer3D({ measurements, onPartClick }) {
  return (
    <div style={{ width: '100%', height: '100%', background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)' }}>
      <Canvas
        camera={{ position: [0, 1.2, 3], fov: 50 }}
        shadows
        dpr={[1, 2]}
      >
        <Scene measurements={measurements} onPartClick={onPartClick} />
      </Canvas>
    </div>
  )
}
