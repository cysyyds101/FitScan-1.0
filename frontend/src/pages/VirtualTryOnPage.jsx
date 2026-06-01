import VirtualTryOn from '../components/VirtualTryOn';

/**
 * VirtualTryOnPage
 * Standalone page component for the virtual try-on feature
 */
export function VirtualTryOnPage() {
  // Preset clothing options (can be loaded from API or static config)
  const presetClothing = [
    { 
      id: 'tshirt-red', 
      name: 'Red T-Shirt', 
      url: '/models/clothing/tshirt_red.glb',
      thumbnail: null
    },
    { 
      id: 'hoodie-blue', 
      name: 'Blue Hoodie', 
      url: '/models/clothing/hoodie_blue.glb',
      thumbnail: null
    },
    { 
      id: 'dress-black', 
      name: 'Black Dress', 
      url: '/models/clothing/dress_black.glb',
      thumbnail: null
    }
  ];
  
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
    // Can be used to update app state or analytics
  };
  
  const handlePhysicsChange = (config) => {
    console.log('Physics config changed:', config);
    // Can be used to update app state or analytics
  };
  
  return (
    <div className="page virtual-tryon-page">
      <div className="page-header">
        <h1>Virtual Try-On</h1>
        <p>Upload your clothing and see how it looks on a 3D model</p>
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
    </div>
  );
}

export default VirtualTryOnPage;
