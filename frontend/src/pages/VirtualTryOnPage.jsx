import VirtualTryOn from '../components/VirtualTryOn';
import { PRESET_CLOTHING, getThumbnailDataUrl } from '../utils/presetClothing';

/**
 * VirtualTryOnPage
 * Standalone page component for the virtual try-on feature
 */
export function VirtualTryOnPage() {
  // Enhance preset clothing with thumbnail data URLs
  const presetClothing = PRESET_CLOTHING.map(item => ({
    ...item,
    thumbnail: getThumbnailDataUrl(item.id) || item.thumbnail
  }));
  
  // Default physics configuration
  const defaultPhysics = {
    stiffness: 0.3,
    dampening: 0.5,
    wind: { x: 0, y: 0, z: 1 },
    gravity: { x: 0, y: -9.8, z: 0 }
  };
  
  // Event handlers
  const handleClothingChange = (clothing) => {
    console.log('Clothing changed:', clothing);
  };
  
  const handlePhysicsChange = (config) => {
    console.log('Physics config changed:', config);
  };
  
  return (
    <div className="page virtual-tryon-page">
      <div className="page-header">
        <h1>虚拟换衣</h1>
        <p>上传您的服装或选择预设服装，查看3D试穿效果</p>
      </div>
      
      <div className="page-content">
        <VirtualTryOn
          humanModelUrl="/models/human/default.glb"
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
      `}</style>
    </div>
  );
}

export default VirtualTryOnPage;
