import { useState, useRef, Suspense, useCallback, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Html, useProgress } from '@react-three/drei';
import * as THREE from 'three';

import { HumanModel, GeometricHumanModel } from './HumanModel';
import { ClothingOverlay } from './ClothingOverlay';
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
 * 集成所有虚拟换衣功能
 * 
 * @param {Object} props
 * @param {string} props.humanModelUrl - 人体模型URL
 * @param {Array} props.presetClothing - 预设服装列表
 * @param {Object} props.defaultPhysics - 默认物理配置
 * @param {boolean} props.showControls - 是否显示控制面板
 * @param {Function} props.onClothingChange - 服装变化回调
 * @param {Function} props.onPhysicsChange - 物理配置变化回调
 */
export function VirtualTryOn({
  humanModelUrl = '/models/human/default.glb',
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
  const [humanModel, setHumanModel] = useState(null);
  const [clothingUrl, setClothingUrl] = useState(null);
  const [clothingModel, setClothingModel] = useState(null);
  const [adjustment, setAdjustment] = useState({
    positionOffset: { x: 0, y: 0, z: 0 },
    rotationOffset: { x: 0, y: 0, z: 0 },
    scale: 1.0
  });
  const [physicsConfig, setPhysicsConfig] = useState(defaultPhysics);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPhysics, setShowPhysics] = useState(true);
  
  // Refs
  const canvasRef = useRef();
  
  // 处理人体模型加载
  const handleHumanModelLoad = useCallback((model) => {
    setHumanModel(model);
    setIsLoading(false);
  }, []);
  
  // 处理人体模型加载错误
  const handleHumanModelError = useCallback((err) => {
    console.error('加载人体模型失败:', err);
    setError(err.message || '加载人体模型失败');
    setIsLoading(false);
  }, []);
  
  // 处理服装上传
  const handleClothingUpload = useCallback((file) => {
    if (!file) return;
    
    // 验证文件类型
    if (!file.name.match(/\.(glb|gltf)$/i)) {
      setError('请上传 GLB 或 GLTF 文件');
      return;
    }
    
    // 验证文件大小 (10MB限制)
    if (file.size > 10 * 1024 * 1024) {
      setError('文件大小必须小于 10MB');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    // 创建本地文件的 blob URL
    const url = URL.createObjectURL(file);
    setClothingUrl(url);
    
    if (onClothingChange) {
      onClothingChange({ url, name: file.name, size: file.size });
    }
  }, [onClothingChange]);
  
  // 处理预设服装选择
  const handlePresetSelect = useCallback((preset) => {
    setIsLoading(true);
    setError(null);
    setClothingUrl(preset.url);
    
    if (onClothingChange) {
      onClothingChange(preset);
    }
  }, [onClothingChange]);
  
  // 处理调整变化
  const handleAdjustmentChange = useCallback((newAdjustment) => {
    setAdjustment(newAdjustment);
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
    setClothingUrl(null);
    setClothingModel(null);
    
    if (onClothingChange) {
      onClothingChange(null);
    }
  }, [onClothingChange]);
  
  // 清除错误
  const handleClearError = useCallback(() => {
    setError(null);
  }, []);
  
  // 组件卸载时清理 blob URL
  useEffect(() => {
    return () => {
      if (clothingUrl && clothingUrl.startsWith('blob:')) {
        URL.revokeObjectURL(clothingUrl);
      }
    };
  }, [clothingUrl]);
  
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
            {/* 人体模型 - 如果没有GLB则使用几何体 */}
            {humanModelUrl ? (
              <HumanModel
                modelUrl={humanModelUrl}
                onLoad={handleHumanModelLoad}
                onError={handleHumanModelError}
              />
            ) : (
              <GeometricHumanModel scale={1} />
            )}
            
            {/* 服装叠加 */}
            {clothingUrl && (
              <ClothingOverlay
                clothingUrl={clothingUrl}
                humanModel={humanModel}
                adjustment={adjustment}
                physicsConfig={showPhysics ? physicsConfig : null}
                onLoad={setClothingModel}
                onError={(err) => setError(err?.message || '加载服装失败')}
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
          clothing={clothingModel ? { url: clothingUrl, name: '当前服装' } : null}
          adjustment={adjustment}
          physicsConfig={physicsConfig}
          showPhysics={showPhysics}
          presets={presetClothing}
          onUpload={handleClothingUpload}
          onPresetSelect={handlePresetSelect}
          onRemove={handleRemoveClothing}
          onAdjustmentChange={handleAdjustmentChange}
          onPhysicsChange={handlePhysicsChange}
          onTogglePhysics={() => setShowPhysics(!showPhysics)}
        />
      )}
      
      {/* 错误提示 */}
      {error && (
        <div className="virtual-tryon-error">
          <span>{error}</span>
          <button onClick={handleClearError}>关闭</button>
        </div>
      )}
    </div>
  );
}

export default VirtualTryOn;
