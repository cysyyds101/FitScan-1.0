import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';

/**
 * GLB Loader Utility
 * Provides centralized loading of 3D models with caching and error handling
 */

let dracoLoader = null;
let gltfLoader = null;

/**
 * Initialize the loaders with DRACO support for compressed models
 * @param {string} dracoPath - Path to DRACO decoder files
 */
export function initializeLoaders(dracoPath = '/draco/') {
  // Create DRACO loader
  dracoLoader = new DRACOLoader();
  dracoLoader.setDecoderPath(dracoPath);
  
  // Create GLTF loader with DRACO support
  gltfLoader = new GLTFLoader();
  gltfLoader.setDRACOLoader(dracoLoader);
  
  return { dracoLoader, gltfLoader };
}

/**
 * Get or create the GLTF loader instance
 * @returns {GLTFLoader}
 */
export function getGLTFLoader() {
  if (!gltfLoader) {
    initializeLoaders();
  }
  return gltfLoader;
}

/**
 * Load a GLB/GLTF model from URL
 * @param {string} url - URL to the model file
 * @param {Function} onProgress - Progress callback (0-100)
 * @param {AbortSignal} signal - Abort signal for cancellation
 * @returns {Promise<THREE.Group>} The loaded model
 */
export async function loadModel(url, onProgress, signal) {
  const loader = getGLTFLoader();
  
  return new Promise((resolve, reject) => {
    // Check if aborted
    if (signal?.aborted) {
      reject(new Error('Load cancelled'));
      return;
    }
    
    // Add abort handler
    const onAbort = () => {
      reject(new Error('Load cancelled'));
    };
    signal?.addEventListener('abort', onAbort);
    
    loader.load(
      url,
      (gltf) => {
        signal?.removeEventListener('abort', onAbort);
        resolve(gltf);
      },
      (progress) => {
        if (onProgress && progress.total > 0) {
          const percent = (progress.loaded / progress.total) * 100;
          onProgress(percent);
        }
      },
      (error) => {
        signal?.removeEventListener('abort', onAbort);
        reject(error);
      }
    );
  });
}

/**
 * Process a loaded GLTF scene for optimal rendering
 * @param {THREE.Group} model - The loaded model
 * @param {Object} options - Processing options
 * @returns {THREE.Group} The processed model
 */
export function processModel(model, options = {}) {
  const {
    enableShadows = true,
    normalizeScale = true,
    centerModel = true,
    targetHeight = 1.7
  } = options;
  
  model.traverse((child) => {
    if (child.isMesh) {
      if (enableShadows) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
      
      if (child.material) {
        child.material.side = THREE.DoubleSide;
        
        // Optimize material
        if (child.material.envMapIntensity !== undefined) {
          child.material.envMapIntensity = 1;
        }
      }
    }
  });
  
  // Normalize scale
  if (normalizeScale) {
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    
    if (size.y > 0) {
      const scaleFactor = targetHeight / size.y;
      model.scale.setScalar(scaleFactor);
    }
  }
  
  // Center model
  if (centerModel) {
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    
    model.position.x = -center.x;
    model.position.z = -center.z;
    model.position.y = -box.min.y; // Sit on ground
  }
  
  return model;
}

/**
 * Extract animation clips from loaded GLTF
 * @param {Object} gltf - The loaded GLTF object
 * @returns {AnimationClip[]} Array of animation clips
 */
export function extractAnimations(gltf) {
  if (!gltf.animations || gltf.animations.length === 0) {
    return [];
  }
  return Array.from(gltf.animations);
}

/**
 * Find a specific mesh or bone in the model
 * @param {THREE.Object3D} object - Parent object to search
 * @param {string} name - Name to search for
 * @returns {THREE.Object3D|null}
 */
export function findByName(object, name) {
  let result = null;
  
  object.traverse((child) => {
    if (child.name === name && !result) {
      result = child;
    }
  });
  
  return result;
}

/**
 * Find all meshes in the model
 * @param {THREE.Object3D} object - Parent object to search
 * @returns {THREE.Mesh[]}
 */
export function findAllMeshes(object) {
  const meshes = [];
  
  object.traverse((child) => {
    if (child.isMesh) {
      meshes.push(child);
    }
  });
  
  return meshes;
}

/**
 * Get model statistics
 * @param {THREE.Object3D} model - The model to analyze
 * @returns {Object} Statistics about the model
 */
export function getModelStats(model) {
  let triangleCount = 0;
  let meshCount = 0;
  let textureCount = 0;
  let boneCount = 0;
  
  model.traverse((child) => {
    if (child.isMesh) {
      meshCount++;
      
      if (child.geometry) {
        const index = child.geometry.index;
        if (index) {
          triangleCount += index.count / 3;
        } else if (child.geometry.attributes.position) {
          triangleCount += child.geometry.attributes.position.count / 3;
        }
      }
      
      if (child.material) {
        const materials = Array.isArray(child.material) 
          ? child.material 
          : [child.material];
        
        materials.forEach((mat) => {
          if (mat.map) textureCount++;
          if (mat.normalMap) textureCount++;
          if (mat.roughnessMap) textureCount++;
        });
      }
    }
    
    if (child.isBone) {
      boneCount++;
    }
  });
  
  return {
    triangleCount: Math.round(triangleCount),
    meshCount,
    textureCount,
    boneCount
  };
}

/**
 * Validate if a model file is supported
 * @param {string} filename - The filename to check
 * @returns {boolean}
 */
export function isValidModelFile(filename) {
  const validExtensions = ['.glb', '.gltf'];
  const ext = filename.toLowerCase().slice(filename.lastIndexOf('.'));
  return validExtensions.includes(ext);
}

/**
 * Check if file size is within limits
 * @param {number} sizeInBytes - File size in bytes
 * @param {number} maxSizeMB - Maximum allowed size in MB
 * @returns {boolean}
 */
export function isFileSizeValid(sizeInBytes, maxSizeMB = 10) {
  const maxBytes = maxSizeMB * 1024 * 1024;
  return sizeInBytes <= maxBytes;
}

// Cache for loaded models
const modelCache = new Map();

/**
 * Load a model with caching
 * @param {string} url - Model URL
 * @param {boolean} useCache - Whether to use cached version
 * @returns {Promise<THREE.Group>}
 */
export async function loadModelCached(url, useCache = true) {
  if (useCache && modelCache.has(url)) {
    // Return clone of cached model
    const cached = modelCache.get(url);
    return cached.clone();
  }
  
  const gltf = await loadModel(url);
  const model = gltf.scene;
  
  if (useCache) {
    modelCache.set(url, model);
  }
  
  return model;
}

/**
 * Clear the model cache
 */
export function clearCache() {
  modelCache.forEach((model) => {
    model.traverse((child) => {
      if (child.geometry) {
        child.geometry.dispose();
      }
      if (child.material) {
        const materials = Array.isArray(child.material)
          ? child.material
          : [child.material];
        materials.forEach((mat) => mat.dispose());
      }
    });
  });
  modelCache.clear();
}

export default {
  initializeLoaders,
  getGLTFLoader,
  loadModel,
  loadModelCached,
  processModel,
  extractAnimations,
  findByName,
  findAllMeshes,
  getModelStats,
  isValidModelFile,
  isFileSizeValid,
  clearCache
};
