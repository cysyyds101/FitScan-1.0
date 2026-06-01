import { useRef, useEffect, useCallback, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { SimpleCloth } from 'three-simplecloth';

/**
 * ClothPhysics Component
 * Wraps three-simplecloth for cloth simulation on clothing meshes
 * 
 * @param {Object} props
 * @param {THREE.SkinnedMesh} props.clothingMesh - The clothing mesh to simulate
 * @param {Object} props.config - Physics configuration
 * @param {THREE.Object3D} props.collidersRoot - Object containing colliders
 * @param {Function} props.onError - Error callback
 */
export function ClothPhysics({
  clothingMesh,
  config = {
    stiffness: 0.3,
    dampening: 0.5,
    windPerSecond: new THREE.Vector3(0, 0, 1),
    gravityPerSecond: new THREE.Vector3(0, -9.8, 0)
  },
  collidersRoot = null,
  onError
}) {
  const clothRef = useRef(null);
  const { gl } = useThree();
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState(null);
  
  // Initialize cloth simulation
  useEffect(() => {
    if (!clothingMesh || !gl) return;
    
    let cloth = null;
    let isMounted = true;
    
    const initCloth = async () => {
      try {
        // Check if WebGPU is available
        const canvas = gl.domElement;
        const context = canvas.getContext('webgpu');
        
        if (!context) {
          console.warn('WebGPU not available, cloth physics disabled');
          setError('WebGPU not supported - cloth physics disabled');
          return;
        }
        
        // Create cloth simulation on the mesh
        cloth = SimpleCloth.onSkinnedMesh(clothingMesh, gl, {
          stiffness: config.stiffness || 0.3,
          dampening: config.dampening || 0.5,
          windPerSecond: new THREE.Vector3(
            config.wind?.x || 0,
            config.wind?.y || 0,
            config.wind?.z || 1
          ),
          gravityPerSecond: new THREE.Vector3(
            config.gravity?.x || 0,
            config.gravity?.y || -9.8,
            config.gravity?.z || 0
          ),
          collidersRoot: collidersRoot
        });
        
        if (isMounted) {
          clothRef.current = cloth;
          setIsInitialized(true);
        }
      } catch (err) {
        console.error('Failed to initialize cloth simulation:', err);
        if (isMounted) {
          setError(err.message);
          if (onError) onError(err);
        }
      }
    };
    
    initCloth();
    
    return () => {
      isMounted = false;
      if (cloth) {
        cloth.dispose?.();
      }
    };
  }, [clothingMesh, gl, config, collidersRoot, onError]);
  
  // Update physics config
  useEffect(() => {
    if (!clothRef.current) return;
    
    const cloth = clothRef.current;
    
    if (config.stiffness !== undefined) {
      cloth.stiffness = config.stiffness;
    }
    if (config.dampening !== undefined) {
      cloth.dampening = config.dampening;
    }
    if (config.wind) {
      cloth.setWind?.(new THREE.Vector3(config.wind.x, config.wind.y, config.wind.z));
    }
    if (config.gravity) {
      cloth.setGravity?.(new THREE.Vector3(config.gravity.x, config.gravity.y, config.gravity.z));
    }
  }, [config]);
  
  // Update loop
  useFrame((state, delta) => {
    if (clothRef.current && isInitialized) {
      clothRef.current.update(delta);
    }
  });
  
  // Return cleanup function
  const dispose = useCallback(() => {
    if (clothRef.current) {
      clothRef.current.dispose?.();
      clothRef.current = null;
    }
  }, []);
  
  // Return API
  return {
    cloth: clothRef.current,
    isInitialized,
    error,
    dispose,
    setWind: (wind) => {
      if (clothRef.current?.setWind) {
        clothRef.current.setWind(wind);
      }
    },
    setGravity: (gravity) => {
      if (clothRef.current?.setGravity) {
        clothRef.current.setGravity(gravity);
      }
    }
  };
}

/**
 * Hook for cloth physics simulation
 */
export function useClothPhysics(clothingMesh, config, collidersRoot) {
  const physics = ClothPhysics({
    clothingMesh,
    config,
    collidersRoot
  });
  
  return physics;
}

export default ClothPhysics;
