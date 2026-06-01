import VirtualTryOn from '../components/VirtualTryOn';
import { PRESET_CLOTHING } from '../utils/presetClothing';

/**
 * VirtualTryOnPage
 * 虚拟换衣页面 - 展示3D人体模型和预设服装
 */
export function VirtualTryOnPage() {
  // 使用预设服装
  const presetClothing = PRESET_CLOTHING;
  
  // 默认物理配置
  const defaultPhysics = {
    stiffness: 0.3,
    dampening: 0.5,
    wind: { x: 0, y: 0, z: 1 },
    gravity: { x: 0, y: -9.8, z: 0 }
  };
  
  // 服装变化处理
  const handleClothingChange = (clothing) => {
    if (clothing) {
      console.log('已选择服装:', clothing.name);
    }
  };
  
  // 物理配置变化处理
  const handlePhysicsChange = (config) => {
    console.log('物理配置:', config);
  };
  
  return (
    <div className="page virtual-tryon-page">
      <div className="page-header">
        <h1>虚拟换衣</h1>
        <p>选择下方预设服装，查看3D试穿效果</p>
      </div>
      
      <div className="page-content">
        <VirtualTryOn
          presetClothing={presetClothing}
          defaultPhysics={defaultPhysics}
          showControls={true}
          onClothingChange={handleClothingChange}
          onPhysicsChange={handlePhysicsChange}
        />
      </div>
      
      <style>{`
        .virtual-tryon-page {
          height: calc(100vh - 120px);
          display: flex;
          flex-direction: column;
        }
        
        .virtual-tryon-page .page-header {
          text-align: center;
          padding: 20px 0;
        }
        
        .virtual-tryon-page .page-header h1 {
          margin: 0 0 8px 0;
          font-size: 28px;
          color: #333;
        }
        
        .virtual-tryon-page .page-header p {
          margin: 0;
          color: #666;
          font-size: 14px;
        }
        
        .virtual-tryon-page .page-content {
          flex: 1;
          display: flex;
          min-height: 0;
        }
        
        .virtual-tryon-page .virtual-tryon-container {
          flex: 1;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .virtual-tryon-page .clothing-controls {
          background: white;
        }
        
        /* 提示文字 */
        .virtual-tryon-hint {
          text-align: center;
          color: #888;
          font-size: 12px;
          padding: 8px 16px;
          background: #f5f5f5;
          border-radius: 8px;
          margin-top: 12px;
        }
      `}</style>
    </div>
  );
}

export default VirtualTryOnPage;
