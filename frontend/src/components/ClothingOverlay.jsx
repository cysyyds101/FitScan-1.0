import { useState, useEffect, useRef, useMemo } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

/**
 * ClothingOverlay Component
 * Loads and positions a clothing model on the human model
 * 
 * @param {Object} props
 * @param {string} props.clothingUrl - URL or blob URL to clothing GLB
 * @param {THREE.Object3D} props.humanModel - The human model to attach to
 * @param {Object} props.adjustment - Position/rotation/scale adjustments
 * @param {Object} props.physicsConfig - Physics configuration for cloth simulation
 * @param {Function} props.onLoad - Callback when clothing loads
 * @param {Function} props.onError - Callback on error
 */
export function ClothingOverlay({
  clothingUrl,
  humanModel,
  adjustment = {
    positionOffset: { x: 0, y: 0, z: 0 },
    rotationOffset: { x: 0, y: 0, z: 0 },
    scale: 1.0
  },
  physicsConfig = null,
  onLoad,
  onError
}) {
  const groupRef = useRef();
  const [clothing, setClothing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Load clothing model
  useEffect(() => {
    if (!clothingUrl) return;
    
    let mounted = true;
    let currentClothing = null;
    
    const loadClothing = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const loader = new GLTFLoader();
        
        const gltf = await new Promise((resolve, reject) => {
          loader.load(
            clothingUrl,
            (gltf) => resolve(gltf),
            (progress) => {
              console.log(`Clothing load progress: ${(progress.loaded / progress.total * 100).toFixed(1)}%`);
            },
            (err) => reject(err)
          );
        });
        
        if (!mounted) return;
        
        currentClothing = gltf.scene;
        
        // Process the clothing model
        currentClothing.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            
            if (child.material) {
              child.material.side = THREE.DoubleSide;
            }
          }
        });
        
        // Apply initial positioning based on adjustment
        applyAdjustment(currentClothing, adjustment);
        
        setClothing(currentClothing);
        setLoading(false);
        
        if (onLoad) {
          onLoad(currentClothing);
        }
        
      } catch (err) {
        if (!mounted) return;
        
        console.error('Failed to load clothing:', err);
        setError(err.message || 'Failed to load clothing');
        setLoading(false);
        
        if (onError) {
          onError(err);
        }
      }
    };
    
    loadClothing();
    
    return () => {
      mounted = false;
    };
  }, [clothingUrl]);
  
  // Update adjustment when it changes
  useEffect(() => {
    if (clothing) {
      applyAdjustment(clothing, adjustment);
    }
  }, [adjustment, clothing]);
  
  // Apply adjustment to the clothing model
  const applyAdjustment = (model, adj) => {
    if (!model) return;
    
    // Position offset
    model.position.x = adj.positionOffset?.x || 0;
    model.position.y = adj.positionOffset?.y || 0;
    model.position.z = adj.positionOffset?.z || 0;
    
    // Rotation offset (convert degrees to radians)
    model.rotation.x = THREE.MathUtils.degToRad(adj.rotationOffset?.x || 0);
    model.rotation.y = THREE.MathUtils.degToRad(adj.rotationOffset?.y || 0);
    model.rotation.z = THREE.MathUtils.degToRad(adj.rotationOffset?.z || 0);
    
    // Scale
    model.scale.setScalar(adj.scale || 1.0);
  };
  
  // Attach to human model if available
  useEffect(() => {
    if (clothing && humanModel) {
      // Parent the clothing to the human model
      humanModel.add(clothing);
      
      return () => {
        humanModel.remove(clothing);
      };
    }
  }, [clothing, humanModel]);
  
  if (loading || error) {
    return null;
  }
  
  return (
    <group ref={groupRef}>
      {clothing && <primitive object={clothing} />}
    </group>
  );
}

/**
 * Simple Clothing Model Display (without physics)
 * Alternative component for simpler use cases
 */
export function SimpleClothingOverlay({
  clothingUrl,
  position = [0, 0, 0],
  rotation = [0, 0, 0],
  scale = 1
}) {
  const [clothing, setClothing] = useState(null);
  
  useEffect(() => {
    if (!clothingUrl) return;
    
    const loader = new GLTFLoader();
    loader.load(clothingUrl, (gltf) => {
      const model = gltf.scene;
      
      model.traverse((child) => {
        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
        }
      });
      
      setClothing(model);
    });
  }, [clothingUrl]);
  
  if (!clothing) return null;
  
  return (
    <group position={position} rotation={rotation} scale={scale}>
      <primitive object={clothing} />
    </group>
  );
}

export default ClothingOverlay;
