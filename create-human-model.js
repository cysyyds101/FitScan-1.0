/**
 * Script to generate a simple humanoid model with cloth-ready vertex colors
 * Run: node create-human-model.js
 */

import * as THREE from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Colors for vertex painting
const WHITE = new THREE.Color(1, 1, 1);      // Static parts (attached to bones)
const RED = new THREE.Color(1, 0, 0);         // Cloth simulation parts

/**
 * Create a humanoid model with vertex colors for cloth simulation
 */
function createHumanoidModel() {
  const group = new THREE.Group();
  group.name = 'Humanoid';
  
  // Materials with vertex colors enabled
  const skinMaterial = new THREE.MeshStandardMaterial({
    color: 0xe8c4a0,
    vertexColors: true,
    side: THREE.DoubleSide
  });
  
  const bodyMaterial = new THREE.MeshStandardMaterial({
    color: 0x4a90d9,
    vertexColors: true,
    side: THREE.DoubleSide
  });
  
  const pantsMaterial = new THREE.MeshStandardMaterial({
    color: 0x2c3e50,
    vertexColors: true,
    side: THREE.DoubleSide
  });
  
  // Helper to apply vertex colors to geometry
  const applyVertexColors = (geometry, color) => {
    const count = geometry.attributes.position.count;
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  };
  
  // Create body parts with WHITE (static) vertices
  
  // Head
  const headGeo = new THREE.SphereGeometry(0.12, 32, 32);
  applyVertexColors(headGeo, WHITE);
  const head = new THREE.Mesh(headGeo, skinMaterial);
  head.position.set(0, 1.5, 0);
  head.name = 'Head';
  group.add(head);
  
  // Neck
  const neckGeo = new THREE.CylinderGeometry(0.05, 0.06, 0.1, 16);
  applyVertexColors(neckGeo, WHITE);
  const neck = new THREE.Mesh(neckGeo, skinMaterial);
  neck.position.set(0, 1.35, 0);
  neck.name = 'Neck';
  group.add(neck);
  
  // Torso (will have shirt attached)
  const torsoGeo = new THREE.CapsuleGeometry(0.2, 0.4, 8, 16);
  applyVertexColors(torsoGeo, WHITE);
  const torso = new THREE.Mesh(torsoGeo, bodyMaterial);
  torso.position.set(0, 1.0, 0);
  torso.name = 'Torso';
  group.add(torso);
  
  // Upper arms (will have shirt sleeves)
  const leftArmGeo = new THREE.CapsuleGeometry(0.05, 0.35, 8, 16);
  applyVertexColors(leftArmGeo, WHITE);
  const leftArm = new THREE.Mesh(leftArmGeo, bodyMaterial);
  leftArm.position.set(-0.3, 1.0, 0);
  leftArm.rotation.z = 0.3;
  leftArm.name = 'LeftArm';
  group.add(leftArm);
  
  const rightArmGeo = new THREE.CapsuleGeometry(0.05, 0.35, 8, 16);
  applyVertexColors(rightArmGeo, WHITE);
  const rightArm = new THREE.Mesh(rightArmGeo, bodyMaterial);
  rightArm.position.set(0.3, 1.0, 0);
  rightArm.rotation.z = -0.3;
  rightArm.name = 'RightArm';
  group.add(rightArm);
  
  // Lower arms (hands)
  const leftForearmGeo = new THREE.CapsuleGeometry(0.04, 0.3, 8, 16);
  applyVertexColors(leftForearmGeo, WHITE);
  const leftForearm = new THREE.Mesh(leftForearmGeo, skinMaterial);
  leftForearm.position.set(-0.45, 0.75, 0);
  leftForearm.name = 'LeftForearm';
  group.add(leftForearm);
  
  const rightForearmGeo = new THREE.CapsuleGeometry(0.04, 0.3, 8, 16);
  applyVertexColors(rightForearmGeo, WHITE);
  const rightForearm = new THREE.Mesh(rightForearmGeo, skinMaterial);
  rightForearm.position.set(0.45, 0.75, 0);
  rightForearm.name = 'RightForearm';
  group.add(rightForearm);
  
  // Upper legs
  const leftThighGeo = new THREE.CapsuleGeometry(0.08, 0.4, 8, 16);
  applyVertexColors(leftThighGeo, WHITE);
  const leftThigh = new THREE.Mesh(leftThighGeo, pantsMaterial);
  leftThigh.position.set(-0.1, 0.5, 0);
  leftThigh.name = 'LeftThigh';
  group.add(leftThigh);
  
  const rightThighGeo = new THREE.CapsuleGeometry(0.08, 0.4, 8, 16);
  applyVertexColors(rightThighGeo, WHITE);
  const rightThigh = new THREE.Mesh(rightThighGeo, pantsMaterial);
  rightThigh.position.set(0.1, 0.5, 0);
  rightThigh.name = 'RightThigh';
  group.add(rightThigh);
  
  // Lower legs
  const leftShinGeo = new THREE.CapsuleGeometry(0.06, 0.4, 8, 16);
  applyVertexColors(leftShinGeo, WHITE);
  const leftShin = new THREE.Mesh(leftShinGeo, pantsMaterial);
  leftShin.position.set(-0.1, 0.15, 0);
  leftShin.name = 'LeftShin';
  group.add(leftShin);
  
  const rightShinGeo = new THREE.CapsuleGeometry(0.06, 0.4, 8, 16);
  applyVertexColors(rightShinGeo, WHITE);
  const rightShin = new THREE.Mesh(rightShinGeo, pantsMaterial);
  rightShin.position.set(0.1, 0.15, 0);
  rightShin.name = 'RightShin';
  group.add(rightShin);
  
  return group;
}

/**
 * Create a t-shirt model with vertex colors for cloth simulation
 * Red = cloth simulation area, White = attached to bones
 */
function createTShirtModel() {
  const group = new THREE.Group();
  group.name = 'TShirt';
  
  // Material with vertex colors
  const material = new THREE.MeshStandardMaterial({
    color: 0xe74c3c,
    vertexColors: true,
    side: THREE.DoubleSide
  });
  
  const applyVertexColors = (geometry, color) => {
    const count = geometry.attributes.position.count;
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  };
  
  // Torso part (WHITE - attached to body)
  const torsoGeo = new THREE.CapsuleGeometry(0.22, 0.35, 8, 16);
  applyVertexColors(torsoGeo, WHITE);
  const torso = new THREE.Mesh(torsoGeo, material);
  torso.position.set(0, 0, 0);
  torso.name = 'ShirtTorso';
  group.add(torso);
  
  // Cloth simulation part - flowing bottom edge (RED)
  const clothGeo = createClothBottomGeometry();
  applyVertexColors(clothGeo, RED);
  const cloth = new THREE.Mesh(clothGeo, material);
  cloth.position.set(0, -0.2, 0);
  cloth.name = 'ShirtCloth';
  group.add(cloth);
  
  // Sleeves (RED - for cloth simulation)
  const leftSleeveGeo = createSleeveGeometry();
  applyVertexColors(leftSleeveGeo, RED);
  const leftSleeve = new THREE.Mesh(leftSleeveGeo, material);
  leftSleeve.position.set(-0.28, 0.1, 0);
  leftSleeve.rotation.z = 0.4;
  leftSleeve.name = 'LeftSleeve';
  group.add(leftSleeve);
  
  const rightSleeveGeo = createSleeveGeometry();
  applyVertexColors(rightSleeveGeo, RED);
  const rightSleeve = new THREE.Mesh(rightSleeveGeo, material);
  rightSleeve.position.set(0.28, 0.1, 0);
  rightSleeve.rotation.z = -0.4;
  rightSleeve.name = 'RightSleeve';
  group.add(rightSleeve);
  
  return group;
}

/**
 * Create cloth bottom edge geometry with wave pattern
 */
function createClothBottomGeometry() {
  const segments = 16;
  const radius = 0.22;
  const height = 0.15;
  const waveAmplitude = 0.02;
  
  const geometry = new THREE.BufferGeometry();
  const vertices = [];
  const indices = [];
  
  // Create vertices in a wave pattern
  for (let i = 0; i <= segments; i++) {
    const angle = (i / segments) * Math.PI * 2;
    const wave = Math.sin(angle * 4) * waveAmplitude;
    
    // Top ring
    vertices.push(
      Math.cos(angle) * radius,
      height,
      Math.sin(angle) * radius
    );
    
    // Bottom ring (with wave)
    vertices.push(
      Math.cos(angle) * radius * (1 + wave),
      0,
      Math.sin(angle) * radius * (1 + wave)
    );
  }
  
  // Create faces
  for (let i = 0; i < segments; i++) {
    const top1 = i * 2;
    const top2 = (i + 1) * 2;
    const bottom1 = i * 2 + 1;
    const bottom2 = (i + 1) * 2 + 1;
    
    indices.push(top1, bottom1, top2);
    indices.push(top2, bottom1, bottom2);
  }
  
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  
  return geometry;
}

/**
 * Create sleeve geometry with flowing end
 */
function createSleeveGeometry() {
  const segments = 8;
  const topRadius = 0.08;
  const bottomRadius = 0.1;
  const length = 0.2;
  
  const geometry = new THREE.CylinderGeometry(
    topRadius, bottomRadius, length, segments, 4, true
  );
  
  return geometry;
}

/**
 * Create a hoodie model
 */
function createHoodieModel() {
  const group = new THREE.Group();
  group.name = 'Hoodie';
  
  const material = new THREE.MeshStandardMaterial({
    color: 0x3498db,
    vertexColors: true,
    side: THREE.DoubleSide
  });
  
  const applyVertexColors = (geometry, color) => {
    const count = geometry.attributes.position.count;
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  };
  
  // Body (WHITE - attached)
  const bodyGeo = new THREE.CapsuleGeometry(0.24, 0.4, 8, 16);
  applyVertexColors(bodyGeo, WHITE);
  const body = new THREE.Mesh(bodyGeo, material);
  body.position.set(0, 0, 0);
  group.add(body);
  
  // Hood (RED - cloth simulation for flowing effect)
  const hoodGeo = new THREE.SphereGeometry(0.15, 16, 16, 0, Math.PI * 2, 0, Math.PI * 0.6);
  applyVertexColors(hoodGeo, RED);
  const hood = new THREE.Mesh(hoodGeo, material);
  hood.position.set(0, 0.35, 0);
  hood.scale.set(1, 0.8, 1);
  group.add(hood);
  
  // Cloth bottom (RED)
  const bottomGeo = createClothBottomGeometry();
  applyVertexColors(bottomGeo, RED);
  const bottom = new THREE.Mesh(bottomGeo, material);
  bottom.position.set(0, -0.25, 0);
  bottom.scale.set(1.1, 1, 1.1);
  group.add(bottom);
  
  return group;
}

/**
 * Create a dress model
 */
function createDressModel() {
  const group = new THREE.Group();
  group.name = 'Dress';
  
  const material = new THREE.MeshStandardMaterial({
    color: 0x9b59b6,
    vertexColors: true,
    side: THREE.DoubleSide
  });
  
  const applyVertexColors = (geometry, color) => {
    const count = geometry.attributes.position.count;
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  };
  
  // Top part (WHITE - attached)
  const topGeo = new THREE.CylinderGeometry(0.15, 0.2, 0.25, 16);
  applyVertexColors(topGeo, WHITE);
  const top = new THREE.Mesh(topGeo, material);
  top.position.set(0, 0.1, 0);
  group.add(top);
  
  // Flowing skirt (RED - full cloth simulation)
  const skirtGeo = createSkirtGeometry();
  applyVertexColors(skirtGeo, RED);
  const skirt = new THREE.Mesh(skirtGeo, material);
  skirt.position.set(0, -0.15, 0);
  group.add(skirt);
  
  return group;
}

/**
 * Create flowing skirt geometry
 */
function createSkirtGeometry() {
  const segments = 24;
  const topRadius = 0.2;
  const bottomRadius = 0.5;
  const height = 0.6;
  
  const geometry = new THREE.CylinderGeometry(
    topRadius, bottomRadius, height, segments, 8, true
  );
  
  // Add wave to bottom edge
  const positions = geometry.attributes.position.array;
  for (let i = 0; i < positions.length; i += 3) {
    const y = positions[i + 1];
    if (y < 0) {
      // Bottom edge - add wave
      const x = positions[i];
      const z = positions[i + 2];
      const dist = Math.sqrt(x * x + z * z);
      const wave = Math.sin(Math.atan2(z, x) * 6) * 0.05;
      positions[i] = x * (1 + wave / dist);
      positions[i + 2] = z * (1 + wave / dist);
    }
  }
  
  geometry.computeVertexNormals();
  return geometry;
}

// Main execution
async function main() {
  console.log('Generating 3D models...\n');
  
  const outputDir = path.join(__dirname, 'frontend', 'public', 'models');
  
  // Ensure directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  // Ensure subdirectories exist
  const humanDir = path.join(outputDir, 'human');
  const clothingDir = path.join(outputDir, 'clothing');
  
  if (!fs.existsSync(humanDir)) {
    fs.mkdirSync(humanDir, { recursive: true });
  }
  if (!fs.existsSync(clothingDir)) {
    fs.mkdirSync(clothingDir, { recursive: true });
  }
  
  // Create exporter
  const exporter = new GLTFExporter();
  
  // Export human model
  console.log('Creating humanoid model...');
  const humanoid = createHumanoidModel();
  
  await new Promise((resolve, reject) => {
    exporter.parse(humanoid, (result) => {
      const buffer = Buffer.from(result);
      fs.writeFileSync(path.join(humanDir, 'default.glb'), buffer);
      console.log('✓ Saved: public/models/human/default.glb\n');
      resolve();
    }, reject, { binary: true });
  });
  
  // Export t-shirt
  console.log('Creating t-shirt model...');
  const tshirt = createTShirtModel();
  
  await new Promise((resolve, reject) => {
    exporter.parse(tshirt, (result) => {
      const buffer = Buffer.from(result);
      fs.writeFileSync(path.join(clothingDir, 'tshirt_red.glb'), buffer);
      console.log('✓ Saved: public/models/clothing/tshirt_red.glb\n');
      resolve();
    }, reject, { binary: true });
  });
  
  // Export hoodie
  console.log('Creating hoodie model...');
  const hoodie = createHoodieModel();
  
  await new Promise((resolve, reject) => {
    exporter.parse(hoodie, (result) => {
      const buffer = Buffer.from(result);
      fs.writeFileSync(path.join(clothingDir, 'hoodie_blue.glb'), buffer);
      console.log('✓ Saved: public/models/clothing/hoodie_blue.glb\n');
      resolve();
    }, reject, { binary: true });
  });
  
  // Export dress
  console.log('Creating dress model...');
  const dress = createDressModel();
  
  await new Promise((resolve, reject) => {
    exporter.parse(dress, (result) => {
      const buffer = Buffer.from(result);
      fs.writeFileSync(path.join(clothingDir, 'dress_purple.glb'), buffer);
      console.log('✓ Saved: public/models/clothing/dress_purple.glb\n');
      resolve();
    }, reject, { binary: true });
  });
  
  console.log('All models generated successfully!');
  console.log('\nModels are ready for the Virtual Try-On feature.');
  console.log('Start the dev server and navigate to /virtual-tryon');
}

main().catch(console.error);
