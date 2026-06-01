import { useState, useRef, Suspense, useCallback, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Html, useProgress } from '@react-three/drei';
import * as THREE from 'three';

import { HumanModel, GeometricHumanModel } from './HumanModel';
import { ClothingOverlay } from './ClothingOverlay';
import { ClothingControls } from './ClothingControls';
import './VirtualTryOn.css';

/**
 * Loading indicator component
 */
function Loader({ progress }) {
  return (
    <Html center>
      <div className="virtual-tryon-loader">
        <div className="loader-spinner"></div>
        <p>Loading 3D Model... {Math.round(progress)}%</p>
      </div>
    </Html>
  );
}

function ProgressBar() {
  const { progress } = useProgress();
  return <Html center>{progress < 100 && <Loader progress={progress} />}</Html>;
}

/**
 * VirtualTryOn Main Component
 * Container component that integrates all virtual try-on functionality
 * 
 * @param {Object} props
 * @param {string} props.humanModelUrl - URL to human GLB model
 * @param {Array} props.presetClothing - Array of preset clothing options
 * @param {Object} props.defaultPhysics - Default physics configuration
 * @param {boolean} props.showControls - Whether to show control panel
 * @param {Function} props.onClothingChange - Callback when clothing changes
 * @param {Function} props.onPhysicsChange - Callback when physics changes
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
  // State
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
  
  // Handle human model load
  const handleHumanModelLoad = useCallback((model) => {
    setHumanModel(model);
    setIsLoading(false);
  }, []);
  
  // Handle human model error
  const handleHumanModelError = useCallback((err) => {
    console.error('Failed to load human model:', err);
    setError(err.message || 'Failed to load human model');
    setIsLoading(false);
  }, []);
  
  // Handle clothing upload
  const handleClothingUpload = useCallback((file) => {
    if (!file) return;
    
    // Validate file type
    if (!file.name.match(/\.(glb|gltf)$/i)) {
      setError('Please upload a GLB or GLTF file');
      return;
    }
    
    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    // Create blob URL for local file
    const url = URL.createObjectURL(file);
    setClothingUrl(url);
    
    if (onClothingChange) {
      onClothingChange({ url, name: file.name, size: file.size });
    }
  }, [onClothingChange]);
  
  // Handle preset clothing selection
  const handlePresetSelect = useCallback((preset) => {
    setIsLoading(true);
    setError(null);
    setClothingUrl(preset.url);
    
    if (onClothingChange) {
      onClothingChange(preset);
    }
  }, [onClothingChange]);
  
  // Handle adjustment changes
  const handleAdjustmentChange = useCallback((newAdjustment) => {
    setAdjustment(newAdjustment);
  }, []);
  
  // Handle physics config changes
  const handlePhysicsChange = useCallback((newConfig) => {
    setPhysicsConfig(newConfig);
    if (onPhysicsChange) {
      onPhysicsChange(newConfig);
    }
  }, [onPhysicsChange]);
  
  // Handle clothing removal
  const handleRemoveClothing = useCallback(() => {
    setClothingUrl(null);
    setClothingModel(null);
    
    if (onClothingChange) {
      onClothingChange(null);
    }
  }, [onClothingChange]);
  
  // Clear error
  const handleClearError = useCallback(() => {
    setError(null);
  }, []);
  
  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (clothingUrl && clothingUrl.startsWith('blob:')) {
        URL.revokeObjectURL(clothingUrl);
      }
    };
  }, [clothingUrl]);
  
  return (
    <div className="virtual-tryon-container">
      {/* 3D Canvas */}
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
          
          {/* Lighting */}
          <ambientLight intensity={0.5} />
          <directionalLight
            position={[5, 5, 5]}
            intensity={1}
            castShadow
            shadow-mapSize={[2048, 2048]}
          />
          <directionalLight position={[-5, 5, -5]} intensity={0.5} />
          
          {/* Environment */}
          <Environment preset="city" />
          
          {/* Loading Progress */}
          <ProgressBar />
          
          <Suspense fallback={null}>
            {/* Human Model - use geometric if no GLB available */}
            {humanModelUrl ? (
              <HumanModel
                modelUrl={humanModelUrl}
                onLoad={handleHumanModelLoad}
                onError={handleHumanModelError}
              />
            ) : (
              <GeometricHumanModel scale={1} />
            )}
            
            {/* Clothing Overlay */}
            {clothingUrl && (
              <ClothingOverlay
                clothingUrl={clothingUrl}
                humanModel={humanModel}
                adjustment={adjustment}
                physicsConfig={showPhysics ? physicsConfig : null}
                onLoad={setClothingModel}
                onError={setError}
              />
            )}
          </Suspense>
          
          {/* Ground Shadow */}
          <ContactShadows
            position={[0, -0.01, 0]}
            opacity={0.4}
            scale={10}
            blur={2}
            far={4}
          />
          
          {/* Controls */}
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
      
      {/* Control Panel */}
      {showControls && (
        <ClothingControls
          clothing={clothingModel ? { url: clothingUrl, name: 'Current Clothing' } : null}
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
      
      {/* Error Display */}
      {error && (
        <div className="virtual-tryon-error">
          <span>{error}</span>
          <button onClick={handleClearError}>Dismiss</button>
        </div>
      )}
    </div>
  );
}

export default VirtualTryOn;
