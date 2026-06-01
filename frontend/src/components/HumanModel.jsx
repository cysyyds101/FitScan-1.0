import { useState, useEffect, useRef } from 'react';
import { useGLTF, useAnimations } from '@react-three/drei';
import * as THREE from 'three';

/**
 * HumanModel Component
 * Loads and displays a 3D human body model from GLB file
 * 
 * @param {string} modelUrl - Path to the GLB model file
 * @param {Object} position - Initial position [x, y, z]
 * @param {Object} scale - Initial scale
 * @param {Function} onLoad - Callback when model loads
 * @param {Function} onError - Callback on load error
 */
export function HumanModel({ 
  modelUrl = '/models/human/default.glb',
  position = [0, 0, 0],
  scale = [1, 1, 1],
  onLoad,
  onError 
}) {
  const groupRef = useRef();
  const [model, setModel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Load the GLB model
  useEffect(() => {
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
              // Progress callback
              console.log(`Loading: ${(progress.loaded / progress.total * 100).toFixed(1)}%`);
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
            // Enable shadows
            child.castShadow = true;
            child.receiveShadow = true;
            
            // Ensure material properties
            if (child.material) {
              child.material.side = THREE.DoubleSide;
            }
          }
          
          if (child.isSkinnedMesh) {
            // Configure skinned mesh
            child.castShadow = true;
            child.receiveShadow = true;
          }
        });
        
        // Normalize model scale and position
        normalizeModel(loadedModel);
        
        setModel(loadedModel);
        setLoading(false);
        
        if (onLoad) {
          onLoad(loadedModel);
        }
        
        // Preload for better performance
        useGLTF.preload(modelUrl);
        
      } catch (err) {
        if (!mounted) return;
        
        console.error('Failed to load human model:', err);
        setError(err.message || 'Failed to load model');
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
    // Calculate bounding box
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    
    // Scale to fit height of 1.7 meters (average human height)
    const targetHeight = 1.7;
    const currentHeight = size.y;
    const scaleFactor = targetHeight / currentHeight;
    
    model.scale.setScalar(scaleFactor);
    
    // Recalculate after scaling
    box.setFromObject(model);
    const newCenter = box.getCenter(new THREE.Vector3());
    
    // Center the model at origin, sitting on the ground
    model.position.x = -newCenter.x;
    model.position.y = -box.min.y; // Place on ground
    model.position.z = -newCenter.z;
  };
  
  if (loading) {
    return null;
  }
  
  if (error) {
    console.warn('HumanModel error:', error);
    return null;
  }
  
  return (
    <group ref={groupRef} position={position} scale={scale}>
      <primitive object={model} />
    </group>
  );
}

/**
 * Create a fallback geometric human model
 * Used when no GLB model is available
 */
export function GeometricHumanModel({ position = [0, 0, 0], scale = 1 }) {
  return (
    <group position={position} scale={scale}>
      {/* Head */}
      <mesh position={[0, 1.5, 0]} castShadow>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshStandardMaterial color="#e8c4a0" />
      </mesh>
      
      {/* Neck */}
      <mesh position={[0, 1.35, 0]} castShadow>
        <cylinderGeometry args={[0.05, 0.06, 0.1, 16]} />
        <meshStandardMaterial color="#e8c4a0" />
      </mesh>
      
      {/* Torso */}
      <mesh position={[0, 1.0, 0]} castShadow>
        <capsuleGeometry args={[0.2, 0.4, 8, 16]} />
        <meshStandardMaterial color="#4a90d9" />
      </mesh>
      
      {/* Left Arm */}
      <mesh position={[-0.3, 1.0, 0]} rotation={[0, 0, 0.3]} castShadow>
        <capsuleGeometry args={[0.05, 0.35, 8, 16]} />
        <meshStandardMaterial color="#4a90d9" />
      </mesh>
      
      {/* Right Arm */}
      <mesh position={[0.3, 1.0, 0]} rotation={[0, 0, -0.3]} castShadow>
        <capsuleGeometry args={[0.05, 0.35, 8, 16]} />
        <meshStandardMaterial color="#4a90d9" />
      </mesh>
      
      {/* Left Leg */}
      <mesh position={[-0.1, 0.5, 0]} castShadow>
        <capsuleGeometry args={[0.07, 0.45, 8, 16]} />
        <meshStandardMaterial color="#2c3e50" />
      </mesh>
      
      {/* Right Leg */}
      <mesh position={[0.1, 0.5, 0]} castShadow>
        <capsuleGeometry args={[0.07, 0.45, 8, 16]} />
        <meshStandardMaterial color="#2c3e50" />
      </mesh>
    </group>
  );
}

// Preload hook for performance
export function preloadHumanModel(url) {
  useGLTF.preload(url);
}

export default HumanModel;
