import { useState, useEffect, useRef } from 'react';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

/**
 * GeometricHumanModel Component
 * Creates a simple geometric human body using Three.js primitives
 * This is used as a fallback when no GLB model is available
 */
export function GeometricHumanModel({ position = [0, 0, 0], scale = 1, onLoad }) {
  const groupRef = useRef();
  
  useEffect(() => {
    if (onLoad && groupRef.current) {
      onLoad(groupRef.current);
    }
  }, []);
  
  return (
    <group ref={groupRef} position={position} scale={scale}>
      {/* Head */}
      <mesh position={[0, 1.5, 0]} castShadow receiveShadow>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial color="#e8c4a0" />
      </mesh>
      
      {/* Neck */}
      <mesh position={[0, 1.35, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.05, 0.06, 0.1, 16]} />
        <meshStandardMaterial color="#e8c4a0" />
      </mesh>
      
      {/* Torso */}
      <mesh position={[0, 1.0, 0]} castShadow receiveShadow>
        <capsuleGeometry args={[0.2, 0.4, 8, 16]} />
        <meshStandardMaterial color="#4a90d9" />
      </mesh>
      
      {/* Left Upper Arm */}
      <mesh position={[-0.3, 1.05, 0]} rotation={[0, 0, 0.3]} castShadow receiveShadow>
        <capsuleGeometry args={[0.05, 0.3, 8, 16]} />
        <meshStandardMaterial color="#4a90d9" />
      </mesh>
      
      {/* Right Upper Arm */}
      <mesh position={[0.3, 1.05, 0]} rotation={[0, 0, -0.3]} castShadow receiveShadow>
        <capsuleGeometry args={[0.05, 0.3, 8, 16]} />
        <meshStandardMaterial color="#4a90d9" />
      </mesh>
      
      {/* Left Forearm */}
      <mesh position={[-0.42, 0.78, 0]} rotation={[0, 0, 0.2]} castShadow receiveShadow>
        <capsuleGeometry args={[0.04, 0.28, 8, 16]} />
        <meshStandardMaterial color="#e8c4a0" />
      </mesh>
      
      {/* Right Forearm */}
      <mesh position={[0.42, 0.78, 0]} rotation={[0, 0, -0.2]} castShadow receiveShadow>
        <capsuleGeometry args={[0.04, 0.28, 8, 16]} />
        <meshStandardMaterial color="#e8c4a0" />
      </mesh>
      
      {/* Left Thigh */}
      <mesh position={[-0.1, 0.52, 0]} castShadow receiveShadow>
        <capsuleGeometry args={[0.08, 0.38, 8, 16]} />
        <meshStandardMaterial color="#2c3e50" />
      </mesh>
      
      {/* Right Thigh */}
      <mesh position={[0.1, 0.52, 0]} castShadow receiveShadow>
        <capsuleGeometry args={[0.08, 0.38, 8, 16]} />
        <meshStandardMaterial color="#2c3e50" />
      </mesh>
      
      {/* Left Shin */}
      <mesh position={[-0.1, 0.18, 0]} castShadow receiveShadow>
        <capsuleGeometry args={[0.055, 0.36, 8, 16]} />
        <meshStandardMaterial color="#2c3e50" />
      </mesh>
      
      {/* Right Shin */}
      <mesh position={[0.1, 0.18, 0]} castShadow receiveShadow>
        <capsuleGeometry args={[0.055, 0.36, 8, 16]} />
        <meshStandardMaterial color="#2c3e50" />
      </mesh>
    </group>
  );
}

/**
 * HumanModel Component
 * Loads and displays a 3D human body model from GLB file
 * Falls back to geometric model if GLB loading fails
 * 
 * @param {Object} props
 * @param {string} props.modelUrl - Path to the GLB model file (optional)
 * @param {Array} props.position - Initial position [x, y, z]
 * @param {Array} props.scale - Initial scale
 * @param {Function} props.onLoad - Callback when model loads
 * @param {Function} props.onError - Callback on load error
 */
export function HumanModel({ 
  modelUrl = null,
  position = [0, 0, 0],
  scale = [1, 1, 1],
  onLoad,
  onError 
}) {
  const groupRef = useRef();
  const [model, setModel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [useGeometric, setUseGeometric] = useState(!modelUrl);
  
  // Load the GLB model if URL is provided
  useEffect(() => {
    if (!modelUrl) {
      setUseGeometric(true);
      return;
    }
    
    let mounted = true;
    
    const loadModel = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const gltf = await new Promise((resolve, reject) => {
          const loader = new THREE.GLTFLoader();
          loader.load(
            modelUrl,
            (gltf) => resolve(gltf),
            (progress) => {
              console.log(`Loading human model: ${(progress.loaded / progress.total * 100).toFixed(1)}%`);
            },
            (err) => reject(err)
          );
        });
        
        if (!mounted) return;
        
        // Process the loaded model
        const loadedModel = gltf.scene;
        
        // Traverse and configure model
        loadedModel.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            if (child.material) {
              child.material.side = THREE.DoubleSide;
            }
          }
          if (child.isSkinnedMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
          }
        });
        
        // Normalize model scale and position
        normalizeModel(loadedModel);
        
        setModel(loadedModel);
        setUseGeometric(false);
        setLoading(false);
        
        if (onLoad) {
          onLoad(loadedModel);
        }
        
      } catch (err) {
        if (!mounted) return;
        
        console.warn('Failed to load human model, using geometric fallback:', err.message);
        setError(err.message);
        setUseGeometric(true);
        setLoading(false);
        
        if (onError) {
          onError(err);
        }
      }
    };
    
    loadModel();
    
    return () => {
      mounted = false;
    };
  }, [modelUrl]);
  
  // Normalize model to fit in view
  const normalizeModel = (model) => {
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    
    // Scale to fit height of 1.7 meters
    const targetHeight = 1.7;
    const scaleFactor = targetHeight / size.y;
    
    model.scale.setScalar(scaleFactor);
    
    // Center the model
    box.setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    
    model.position.x = -center.x;
    model.position.y = -box.min.y;
    model.position.z = -center.z;
  };
  
  // Show geometric model while loading
  if (loading || useGeometric) {
    return (
      <GeometricHumanModel 
        position={position} 
        scale={scale} 
        onLoad={onLoad}
      />
    );
  }
  
  // Show loaded GLB model
  if (model) {
    return (
      <group ref={groupRef} position={position} scale={scale}>
        <primitive object={model} />
      </group>
    );
  }
  
  // Fallback to geometric model on error
  return (
    <GeometricHumanModel 
      position={position} 
      scale={scale} 
      onLoad={onLoad}
    />
  );
}

// Preload hook for performance
export function preloadHumanModel(url) {
  useGLTF.preload(url);
}

export default HumanModel;
