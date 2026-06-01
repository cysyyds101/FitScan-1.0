import { useState, useRef, Suspense, useCallback, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Html, useProgress } from '@react-three/drei';
import * as THREE from 'three';

import { GeometricHumanModel } from './HumanModel';
import { GeometricClothing, getAvailableClothingIds } from './GeometricClothing';
import { ClothingControls } from './ClothingControls';
import './VirtualTryOn.css';

/**
 * 加载指示器组件
 */
function Loader({ progress }) {
  return (
    <Html center>
      <div className="virtual-tryon-loader">
        <div className="loader-spinner"></div>
        <p>正在加载3D模型... {Math.round(progress)}%</p>
      </div>
    </Html>
  );
}

function ProgressBar() {
  const { progress } = useProgress();
  return <Html center>{progress < 100 && <Loader progress={progress} />}</Html>;
}

/**
 * 虚拟换衣主组件
 */
export function VirtualTryOn({
  presetClothing = [],
  defaultPhysics = {
    stiffness: 0.3,
    dampening: 0.5,
    wind: { x: 0, y: 0, z: 1 },
    gravity: { x: 0, y: -9.8, z: 0 }
  },
  showControls = true,
  onClothingChange,
  onPhysicsChange
}) {
  // 状态
  const [selectedClothing, setSelectedClothing] = useState(null);
  const [adjustment, setAdjustment] = useState({
    positionOffset: { x: 0, y: 0, z: 0 },
    rotationOffset: { x: 0, y: 0, z: 0 },
    scale: 1.0
  });
  const [physicsConfig, setPhysicsConfig] = useState(defaultPhysics);
  const [showPhysics, setShowPhysics] = useState(true);
  
  // Refs
  const canvasRef = useRef();
  
  // 处理预设服装选择
  const handlePresetSelect = useCallback((preset) => {
    setSelectedClothing(preset);
    
    if (onClothingChange) {
      onClothingChange(preset);
    }
  }, [onClothingChange]);
  
  // 处理调整变化
  const handleAdjustmentChange = useCallback((newAdjustment) => {
    setAdjustment(newAdjustment);
  }, []);
  
  // 重置调整
  const handleResetAdjustment = useCallback(() => {
    setAdjustment({
      positionOffset: { x: 0, y: 0, z: 0 },
      rotationOffset: { x: 0, y: 0, z: 0 },
      scale: 1.0
    });
  }, []);
  
  // 处理物理配置变化
  const handlePhysicsChange = useCallback((newConfig) => {
    setPhysicsConfig(newConfig);
    if (onPhysicsChange) {
      onPhysicsChange(newConfig);
    }
  }, [onPhysicsChange]);
  
  // 处理服装移除
  const handleRemoveClothing = useCallback(() => {
    setSelectedClothing(null);
    
    if (onClothingChange) {
      onClothingChange(null);
    }
  }, [onClothingChange]);
  
  // 获取服装3D位置
  const getClothingPosition = () => {
    return [
      adjustment.positionOffset.x,
      adjustment.positionOffset.y,
      adjustment.positionOffset.z
    ];
  };
  
  // 获取服装旋转
  const getClothingRotation = () => {
    return [
      THREE.MathUtils.degToRad(adjustment.rotationOffset.x),
      THREE.MathUtils.degToRad(adjustment.rotationOffset.y),
      THREE.MathUtils.degToRad(adjustment.rotationOffset.z)
    ];
  };
  
  return (
    <div className="virtual-tryon-container">
      {/* 3D 画布 */}
      <div className="virtual-tryon-canvas" ref={canvasRef}>
        <Canvas
          shadows
          camera={{ position: [0, 1, 3], fov: 50 }}
          gl={{ 
            antialias: true,
            toneMapping: THREE.ACESFilmicToneMapping,
            toneMappingExposure: 1
          }}
        >
          <color attach="background" args={['#f0f0f0']} />
          
          {/* 灯光 */}
          <ambientLight intensity={0.5} />
          <directionalLight
            position={[5, 5, 5]}
            intensity={1}
            castShadow
            shadow-mapSize={[2048, 2048]}
          />
          <directionalLight position={[-5, 5, -5]} intensity={0.5} />
          
          {/* 环境 */}
          <Environment preset="city" />
          
          {/* 加载进度 */}
          <ProgressBar />
          
          <Suspense fallback={null}>
            {/* 人体模型 */}
            <GeometricHumanModel scale={1} />
            
            {/* 服装模型 */}
            {selectedClothing && (
              <GeometricClothing
                presetId={selectedClothing.id}
                position={getClothingPosition()}
                rotation={getClothingRotation()}
                scale={adjustment.scale}
                selected={true}
              />
            )}
          </Suspense>
          
          {/* 地面阴影 */}
          <ContactShadows
            position={[0, -0.01, 0]}
            opacity={0.4}
            scale={10}
            blur={2}
            far={4}
          />
          
          {/* 控制 */}
          <OrbitControls
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            minDistance={1}
            maxDistance={10}
            minPolarAngle={0}
            maxPolarAngle={Math.PI}
          />
        </Canvas>
      </div>
      
      {/* 控制面板 */}
      {showControls && (
        <ClothingControls
          clothing={selectedClothing}
          adjustment={adjustment}
          physicsConfig={physicsConfig}
          showPhysics={showPhysics}
          presets={presetClothing}
          onUpload={() => {}}
          onPresetSelect={handlePresetSelect}
          onRemove={handleRemoveClothing}
          onAdjustmentChange={handleAdjustmentChange}
          onPhysicsChange={handlePhysicsChange}
          onTogglePhysics={() => setShowPhysics(!showPhysics)}
          onReset={handleResetAdjustment}
        />
      )}
    </div>
  );
}

export default VirtualTryOn;
