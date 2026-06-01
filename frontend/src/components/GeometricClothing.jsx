import { useMemo } from 'react';
import * as THREE from 'three';

/**
 * GeometricClothing Component
 * Creates clothing using Three.js primitives for instant preview
 * No need to load external GLB files
 */

const CLOTHING_CONFIGS = {
  'tshirt-red': {
    color: '#e74c3c',
    type: 'tshirt',
    position: [0, 1.0, 0],
    scale: 0.22
  },
  'hoodie-blue': {
    color: '#3498db',
    type: 'hoodie',
    position: [0, 1.0, 0],
    scale: 0.24
  },
  'dress-purple': {
    color: '#9b59b6',
    type: 'dress',
    position: [0, 0.9, 0],
    scale: 0.2
  }
};

/**
 * T-Shirt Component
 */
function TShirt({ color, scale = 0.22 }) {
  return (
    <group scale={scale}>
      {/* Torso */}
      <mesh position={[0, 0, 0]} castShadow>
        <capsuleGeometry args={[1, 1.5, 8, 16]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Left Sleeve */}
      <mesh position={[-1.1, 0.3, 0]} rotation={[0, 0, 0.5]} castShadow>
        <capsuleGeometry args={[0.25, 0.5, 8, 12]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Right Sleeve */}
      <mesh position={[1.1, 0.3, 0]} rotation={[0, 0, -0.5]} castShadow>
        <capsuleGeometry args={[0.25, 0.5, 8, 12]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Collar */}
      <mesh position={[0, 0.9, 0.1]} rotation={[0.3, 0, 0]} castShadow>
        <torusGeometry args={[0.3, 0.08, 8, 16, Math.PI]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

/**
 * Hoodie Component
 */
function Hoodie({ color, scale = 0.24 }) {
  return (
    <group scale={scale}>
      {/* Body */}
      <mesh position={[0, 0, 0]} castShadow>
        <capsuleGeometry args={[1, 1.6, 8, 16]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Hood */}
      <mesh position={[0, 1.3, 0]} rotation={[-0.3, 0, 0]} castShadow>
        <sphereGeometry args={[0.5, 16, 16, 0, Math.PI * 2, 0, Math.PI * 0.6]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Left Sleeve */}
      <mesh position={[-1.15, 0.3, 0]} rotation={[0, 0, 0.4]} castShadow>
        <capsuleGeometry args={[0.28, 0.6, 8, 12]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Right Sleeve */}
      <mesh position={[1.15, 0.3, 0]} rotation={[0, 0, -0.4]} castShadow>
        <capsuleGeometry args={[0.28, 0.6, 8, 12]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Pocket */}
      <mesh position={[0, -0.5, 0.9]} castShadow>
        <boxGeometry args={[0.8, 0.4, 0.1]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

/**
 * Dress Component
 */
function Dress({ color, scale = 0.2 }) {
  return (
    <group scale={scale}>
      {/* Top */}
      <mesh position={[0, 0.5, 0]} castShadow>
        <cylinderGeometry args={[0.5, 0.7, 0.8, 16]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Skirt */}
      <mesh position={[0, -0.3, 0]} castShadow>
        <cylinderGeometry args={[0.7, 1.8, 2.2, 24]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      
      {/* Straps */}
      <mesh position={[-0.25, 1.1, 0]} rotation={[0, 0, 0.2]} castShadow>
        <cylinderGeometry args={[0.06, 0.06, 0.8, 8]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0.25, 1.1, 0]} rotation={[0, 0, -0.2]} castShadow>
        <cylinderGeometry args={[0.06, 0.06, 0.8, 8]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

/**
 * GeometricClothing Component
 * Renders clothing based on preset ID
 */
export function GeometricClothing({ 
  presetId, 
  position = [0, 0, 0], 
  rotation = [0, 0, 0], 
  scale = 1,
  onClick,
  selected 
}) {
  const config = CLOTHING_CONFIGS[presetId];
  
  if (!config) return null;
  
  const ClothingComponent = {
    'tshirt': TShirt,
    'hoodie': Hoodie,
    'dress': Dress
  }[config.type] || TShirt;
  
  return (
    <group 
      position={position} 
      rotation={rotation}
      scale={scale}
      onClick={onClick}
    >
      <ClothingComponent color={config.color} scale={config.scale} />
      
      {/* Selection highlight */}
      {selected && (
        <mesh>
          <sphereGeometry args={[0.6, 16, 16]} />
          <meshBasicMaterial color="#4a90d9" transparent opacity={0.1} />
        </mesh>
      )}
    </group>
  );
}

/**
 * Get clothing config by ID
 */
export function getClothingConfig(presetId) {
  return CLOTHING_CONFIGS[presetId] || null;
}

/**
 * Get all available clothing IDs
 */
export function getAvailableClothingIds() {
  return Object.keys(CLOTHING_CONFIGS);
}

/**
 * Create clothing material
 */
export function createClothingMaterial(color) {
  return new THREE.MeshStandardMaterial({
    color: color,
    side: THREE.DoubleSide,
    roughness: 0.7,
    metalness: 0.1
  });
}

export default GeometricClothing;
