/**
 * VirtualTryOn.jsx — 虚拟试衣主容器。
 *
 * 职责（按你确认的"extracted_container"方案）：
 *  - 管理服装选中状态 / transform 状态 / 伪布料开关
 *  - 在 R3F <Canvas> 内部组合 HumanModel + ClothingOverlay
 *  - 不包含 Scene（Camera/Light）—— 由 Page 层提供
 *  - 不包含 UI 面板（ClothingControls）—— 由 Page 层组合
 *  - 选中服装切换时自动重置 transform
 *
 * 用法：
 *  <Canvas>
 *    <VirtualTryOn />     ← 放进 Scene.jsx 的 children
 *  </Canvas>
 *
 * 状态以受控 prop 暴露给父级，方便 Page 侧面板读取：
 *  - clothing / setClothing
 *  - transform / setTransform
 *  - vertexOffset / setVertexOffset
 *
 * Page 也可以选择不接 prop，让容器内部自管状态（默认行为）。
 */
import { useState } from 'react';
import HumanModel from './HumanModel';
import ClothingOverlay from './ClothingOverlay';
import ReconstructionViewer from './ReconstructionViewer';
import { DEFAULT_TRANSFORM } from './ClothingControls';

export default function VirtualTryOn(props) {
  const {
    clothing: clothingProp,
    setClothing: setClothingProp,
    transform: transformProp,
    setTransform: setTransformProp,
    vertexOffset: vertexOffsetProp,
    setVertexOffset: setVertexOffsetProp,
    humanGlbUrl,
  } = props ?? {};

  // 当父级没传受控状态时，使用容器内自管 state
  const [internalClothing, setInternalClothing] = useState(null);
  const [internalTransform, setInternalTransform] = useState(DEFAULT_TRANSFORM);
  const [internalVertexOffset, setInternalVertexOffset] = useState(true);

  const clothing = clothingProp ?? internalClothing;
  const transform = transformProp ?? internalTransform;
  const vertexOffset = vertexOffsetProp ?? internalVertexOffset;
  const setClothing = setClothingProp ?? setInternalClothing;
  const setTransform = setTransformProp ?? setInternalTransform;
  const setVertexOffset = setVertexOffsetProp ?? setInternalVertexOffset;

  const selectClothing = (item) => {
    setClothing(item);
    setTransform(DEFAULT_TRANSFORM);
  };

  // 把状态回传：让父级 UI 面板可读
  // （如果父级传了受控回调，状态自然已同步；这里仅暴露给未传 prop 的情况）
  if (props?.onStateChange && !clothingProp) {
    props.onStateChange({ clothing, transform, vertexOffset });
  }

  return (
    <>
      {humanGlbUrl ? (
        <ReconstructionViewer glbUrl={humanGlbUrl}>
          <HumanModel />
        </ReconstructionViewer>
      ) : (
        <HumanModel />
      )}
      {clothing && (
        <ClothingOverlay
          clothing={clothing}
          transform={transform}
          vertexOffset={vertexOffset}
        />
      )}
    </>
  );
}

/**
 * 暴露给 Page 用的辅助 hook。
 * 让 Page 用单一受控 state 容器，避免每个 prop 都透传。
 */
export function useTryOnState() {
  const [clothing, setClothing] = useState(null);
  const [transform, setTransform] = useState(DEFAULT_TRANSFORM);
  const [vertexOffset, setVertexOffset] = useState(true);

  const selectClothing = (item) => {
    setClothing(item);
    setTransform(DEFAULT_TRANSFORM);
  };

  return {
    clothing,
    setClothing,
    selectClothing,
    transform,
    setTransform,
    vertexOffset,
    setVertexOffset,
  };
}
