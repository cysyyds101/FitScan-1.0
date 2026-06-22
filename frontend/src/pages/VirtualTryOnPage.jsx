/**
 * VirtualTryOnPage.jsx — 唯一页面。
 *
 * 职责（Frontend Rule）：
 *  - 页面只负责组合组件，不写任何 Three.js 逻辑
 *  - 提供 Scene（<Canvas> + 灯光/相机）和 UI 布局
 *  - 用 useTryOnState() hook 集中管理 3D 容器和 UI 面板共享的状态
 *  - useReconstructions hook 自动 poll 最新 recon 的 status
 *  - 当最新 recon 是 done 时，把它的 glb_url 喂给 VirtualTryOn
 *    （替换默认 human）
 *
 * 结构：
 *  ┌──────────────────────────────────────┐
 *  │ topbar（标题 + 操作提示）              │
 *  ├──────────────────────────┬───────────┤
 *  │                          │           │
 *  │  <Scene>                 │ 侧边栏    │
 *  │   <VirtualTryOn .../>    │  - 上传/重建│
 *  │  </Scene>                │  - 服装列表│
 *  │                          │  - 控制面板│
 *  └──────────────────────────┴───────────┘
 */
import { useState } from 'react';
import Navbar from '../components/Navbar';
import Scene from '../core/Scene';
import VirtualTryOn, { useTryOnState } from '../components/VirtualTryOn';
import ClothingControls from '../components/ClothingControls';
import ReconstructionPanel from '../components/ReconstructionPanel';
import '../styles/global.css';

export default function VirtualTryOnPage() {
  const {
    clothing,
    selectClothing,
    transform,
    setTransform,
    vertexOffset,
    setVertexOffset,
  } = useTryOnState();

  // uploadId state lives in the page so the panel + viewer share it
  const [uploadId, setUploadId] = useState(null);

  // When the latest recon reaches 'done', feed its glb_url to the 3D viewer
  const [pickedGlbUrl, setPickedGlbUrl] = useState(null);

  return (
    <div className="app">
      <Navbar />

      <main className="main">
        <div className="stage">
          <Scene>
            <VirtualTryOn
              clothing={clothing}
              transform={transform}
              vertexOffset={vertexOffset}
              humanGlbUrl={pickedGlbUrl}
            />
          </Scene>
        </div>

        <aside className="side">
          <ReconstructionPanel
            uploadId={uploadId}
            onUploadId={setUploadId}
            onPickedGlb={setPickedGlbUrl}
          />
          <ClothingControls
            selectedId={clothing?.id}
            onSelect={selectClothing}
            transform={clothing ? transform : undefined}
            setTransform={setTransform}
            vertexOffset={vertexOffset}
            setVertexOffset={setVertexOffset}
          />
        </aside>
      </main>
    </div>
  );
}
