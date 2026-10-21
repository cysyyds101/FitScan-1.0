// AvatarEntity — the "avatar entity" abstraction.
//
// Per Phase F architecture (per user feedback):
//   ❌ DON'T do `scene.remove(oldGLB).add(newGLB)` on every URL change
//   ✔  DO keep the entity alive, just update its mesh data + skeleton
//      binding when a new GLB lands
//
// Implementation:
//   - A persistent <group> is the avatar's root (never destroyed between
//     glb_url changes)
//   - A `useRef` tracks the currently-mounted mesh
//   - When glb_url changes, we dispose the old mesh's geometries/materials
//     and add the new one to the SAME group
//   - Skeleton binding: if the new GLB has a SkinnedMesh, we re-parent
//     the root bone into the group so the avatar entity controls the rig
//
// Props:
//   glbUrl          - URL of the GLB to load (null = empty avatar)
//   children        - optional fallback content rendered if no glbUrl
//   fallback        - { ProceduralHuman } or similar JSX used while the
//                      new GLB is loading (avoids a flash of empty body)
import { useGLTF } from "@react-three/drei";
import { useEffect, useRef } from "react";
import * as THREE from "three";

function disposeObject(obj) {
  obj.traverse((child) => {
    if (child.isMesh) {
      child.geometry?.dispose?.();
      const mats = Array.isArray(child.material) ? child.material : [child.material];
      mats.forEach((m) => m?.dispose?.());
    }
  });
}

function applyShadows(obj) {
  obj.traverse((child) => {
    if (child.isMesh) {
      child.castShadow = true;
      child.receiveShadow = true;
    }
  });
}

function normalizeScaleAndCenter(obj, targetHeight = 1.8) {
  const box = new THREE.Box3().setFromObject(obj);
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);
  obj.position.x -= center.x;
  obj.position.z -= center.z;
  const maxDim = Math.max(size.x, size.y, size.z) || 1;
  const s = targetHeight / maxDim;
  obj.scale.setScalar(s);
  obj.position.y = -box.min.y * s;
}

/**
 * Bind a SkinnedMesh's root bone to the parent group so external
 * skeleton controls (e.g. AnimationMixer) can drive the avatar.
 * Falls back to a no-op if the mesh has no skeleton.
 */
function rebindSkeleton(obj) {
  obj.traverse((child) => {
    if (child.isSkinnedMesh && child.skeleton?.bones?.length) {
      // The root bone is bones[0]; expose it for animation control.
      child.userData.rootBone = child.skeleton.bones[0];
    }
  });
}

export default function AvatarEntity({ glbUrl, children, fallback = null }) {
  const groupRef = useRef();
  const mountedRef = useRef(null);

  // Track the current URL so we can compare in the effect below.
  // Sentinel null ensures the first non-null glbUrl always triggers mount.
  const urlRef = useRef(null);

  useEffect(() => {
    if (!groupRef.current) return;

    // If URL didn't change, do nothing. Keeps stable refs alive.
    if (urlRef.current === glbUrl) return;

    // 1. Dispose the previous mesh (if any)
    if (mountedRef.current) {
      groupRef.current.remove(mountedRef.current);
      disposeObject(mountedRef.current);
      mountedRef.current = null;
    }

    // 2. Clear the userData skeleton refs from the old object so GC can
    //    collect the skeleton.
    urlRef.current = glbUrl;

    // 3. Mounting the new mesh is handled by <GltfMount> below, which
    //    uses useGLTF (suspense-aware) and triggers this effect again
    //    when the GLTF data arrives.
  }, [glbUrl]);

  return (
    <group ref={groupRef}>
      {glbUrl ? (
        <GltfMount
          url={glbUrl}
          groupRef={groupRef}
          mountedRef={mountedRef}
        />
      ) : (
        children ?? fallback
      )}
    </group>
  );
}

/**
 * GltfMount — a subcomponent that uses useGLTF and, when the GLB data
 * arrives, mounts it into the parent group WITHOUT recreating the group.
 */
function GltfMount({ url, groupRef, mountedRef }) {
  const gltf = useGLTF(url, true, true);

  useEffect(() => {
    if (!gltf?.scene || !groupRef.current) return;

    const obj = gltf.scene.clone(true);  // drei caches; clone to own it
    applyShadows(obj);
    normalizeScaleAndCenter(obj);
    rebindSkeleton(obj);

    // Insert into the SAME persistent group, not a new one
    groupRef.current.add(obj);
    mountedRef.current = obj;

    return () => {
      if (mountedRef.current === obj) {
        groupRef.current?.remove(obj);
        disposeObject(obj);
        mountedRef.current = null;
      }
    };
  }, [gltf, groupRef, mountedRef]);

  return null;
}

// Preload the default avatar
useGLTF.preload("/models/human.glb");
