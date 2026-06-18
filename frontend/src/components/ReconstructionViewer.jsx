// ReconstructionViewer — render a recon GLB inside a persistent
// AvatarEntity so the scene's avatar root is NEVER rebuilt on URL change.
//
// This replaces the old "useGLTF inside a fresh component" approach
// that did scene.remove(old).add(new) on every recon update.

import AvatarEntity from "./AvatarEntity";

export default function ReconstructionViewer({ glbUrl, children, fallback = null }) {
  return (
    <AvatarEntity glbUrl={glbUrl ?? null} fallback={fallback}>
      {children}
    </AvatarEntity>
  );
}
