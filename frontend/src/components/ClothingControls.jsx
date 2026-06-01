import { useState, useCallback } from 'react';
import './ClothingControls.css';

/**
 * ClothingControls Component
 * UI panel for controlling clothing position, rotation, scale, and physics
 */
export function ClothingControls({
  clothing,
  adjustment,
  physicsConfig,
  showPhysics,
  presets = [],
  onUpload,
  onPresetSelect,
  onRemove,
  onAdjustmentChange,
  onPhysicsChange,
  onTogglePhysics
}) {
  const [activeTab, setActiveTab] = useState('position');
  
  // Handle file input change
  const handleFileChange = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
    }
  }, [onUpload]);
  
  // Handle slider changes
  const handleSliderChange = useCallback((key, axis, value) => {
    const numValue = parseFloat(value);
    
    if (key === 'adjustment') {
      onAdjustmentChange({
        ...adjustment,
        [axis === 'scale' ? 'scale' : `${axis}Offset`]: 
          axis === 'scale' 
            ? numValue 
            : { ...adjustment[`${axis}Offset`], [key]: numValue }
      });
    } else if (key === 'physics') {
      onPhysicsChange({
        ...physicsConfig,
        [axis]: numValue
      });
    }
  }, [adjustment, physicsConfig, onAdjustmentChange, onPhysicsChange]);
  
  // Handle physics vector slider
  const handleVectorSlider = useCallback((axis, value) => {
    const numValue = parseFloat(value);
    onPhysicsChange({
      ...physicsConfig,
      wind: { ...physicsConfig.wind, [axis]: numValue },
      gravity: axis === 'y' 
        ? { ...physicsConfig.gravity, y: physicsConfig.gravity.y + numValue * 0.1 - physicsConfig.gravity.y }
        : physicsConfig.gravity
    });
  }, [physicsConfig, onPhysicsChange]);
  
  return (
    <div className="clothing-controls">
      {/* Tab Navigation */}
      <div className="controls-tabs">
        <button 
          className={activeTab === 'position' ? 'active' : ''}
          onClick={() => setActiveTab('position')}
        >
          Position
        </button>
        <button 
          className={activeTab === 'rotation' ? 'active' : ''}
          onClick={() => setActiveTab('rotation')}
        >
          Rotation
        </button>
        <button 
          className={activeTab === 'scale' ? 'active' : ''}
          onClick={() => setActiveTab('scale')}
        >
          Scale
        </button>
        {showPhysics && (
          <button 
            className={activeTab === 'physics' ? 'active' : ''}
            onClick={() => setActiveTab('physics')}
          >
            Physics
          </button>
        )}
      </div>
      
      {/* Tab Content */}
      <div className="controls-content">
        {/* Position Tab */}
        {activeTab === 'position' && (
          <div className="control-group">
            <h4>Position Offset</h4>
            
            <div className="slider-control">
              <label>X Axis</label>
              <input
                type="range"
                min="-1"
                max="1"
                step="0.01"
                value={adjustment?.positionOffset?.x || 0}
                onChange={(e) => handleSliderChange('adjustment', 'positionX', e.target.value)}
              />
              <span>{(adjustment?.positionOffset?.x || 0).toFixed(2)}</span>
            </div>
            
            <div className="slider-control">
              <label>Y Axis (Height)</label>
              <input
                type="range"
                min="-1"
                max="1"
                step="0.01"
                value={adjustment?.positionOffset?.y || 0}
                onChange={(e) => handleSliderChange('adjustment', 'positionY', e.target.value)}
              />
              <span>{(adjustment?.positionOffset?.y || 0).toFixed(2)}</span>
            </div>
            
            <div className="slider-control">
              <label>Z Axis (Depth)</label>
              <input
                type="range"
                min="-1"
                max="1"
                step="0.01"
                value={adjustment?.positionOffset?.z || 0}
                onChange={(e) => handleSliderChange('adjustment', 'positionZ', e.target.value)}
              />
              <span>{(adjustment?.positionOffset?.z || 0).toFixed(2)}</span>
            </div>
          </div>
        )}
        
        {/* Rotation Tab */}
        {activeTab === 'rotation' && (
          <div className="control-group">
            <h4>Rotation Offset</h4>
            
            <div className="slider-control">
              <label>X (Pitch)</label>
              <input
                type="range"
                min="-180"
                max="180"
                step="1"
                value={adjustment?.rotationOffset?.x || 0}
                onChange={(e) => handleSliderChange('adjustment', 'rotationX', e.target.value)}
              />
              <span>{(adjustment?.rotationOffset?.x || 0)}°</span>
            </div>
            
            <div className="slider-control">
              <label>Y (Yaw)</label>
              <input
                type="range"
                min="-180"
                max="180"
                step="1"
                value={adjustment?.rotationOffset?.y || 0}
                onChange={(e) => handleSliderChange('adjustment', 'rotationY', e.target.value)}
              />
              <span>{(adjustment?.rotationOffset?.y || 0)}°</span>
            </div>
            
            <div className="slider-control">
              <label>Z (Roll)</label>
              <input
                type="range"
                min="-180"
                max="180"
                step="1"
                value={adjustment?.rotationOffset?.z || 0}
                onChange={(e) => handleSliderChange('adjustment', 'rotationZ', e.target.value)}
              />
              <span>{(adjustment?.rotationOffset?.z || 0)}°</span>
            </div>
          </div>
        )}
        
        {/* Scale Tab */}
        {activeTab === 'scale' && (
          <div className="control-group">
            <h4>Scale</h4>
            
            <div className="slider-control">
              <label>Size</label>
              <input
                type="range"
                min="0.1"
                max="3"
                step="0.01"
                value={adjustment?.scale || 1}
                onChange={(e) => handleSliderChange('adjustment', 'scale', e.target.value)}
              />
              <span>{(adjustment?.scale || 1).toFixed(2)}x</span>
            </div>
          </div>
        )}
        
        {/* Physics Tab */}
        {activeTab === 'physics' && (
          <div className="control-group">
            <h4>Cloth Physics</h4>
            
            <div className="slider-control">
              <label>Stiffness</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={physicsConfig?.stiffness || 0.3}
                onChange={(e) => onPhysicsChange({ ...physicsConfig, stiffness: parseFloat(e.target.value) })}
              />
              <span>{(physicsConfig?.stiffness || 0.3).toFixed(2)}</span>
            </div>
            
            <div className="slider-control">
              <label>Dampening</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={physicsConfig?.dampening || 0.5}
                onChange={(e) => onPhysicsChange({ ...physicsConfig, dampening: parseFloat(e.target.value) })}
              />
              <span>{(physicsConfig?.dampening || 0.5).toFixed(2)}</span>
            </div>
            
            <div className="slider-control">
              <label>Wind X</label>
              <input
                type="range"
                min="-5"
                max="5"
                step="0.1"
                value={physicsConfig?.wind?.x || 0}
                onChange={(e) => onPhysicsChange({ 
                  ...physicsConfig, 
                  wind: { ...physicsConfig.wind, x: parseFloat(e.target.value) }
                })}
              />
              <span>{(physicsConfig?.wind?.x || 0).toFixed(1)}</span>
            </div>
            
            <div className="slider-control">
              <label>Wind Z</label>
              <input
                type="range"
                min="-5"
                max="5"
                step="0.1"
                value={physicsConfig?.wind?.z || 1}
                onChange={(e) => onPhysicsChange({ 
                  ...physicsConfig, 
                  wind: { ...physicsConfig.wind, z: parseFloat(e.target.value) }
                })}
              />
              <span>{(physicsConfig?.wind?.z || 1).toFixed(1)}</span>
            </div>
            
            <button 
              className="physics-toggle"
              onClick={onTogglePhysics}
            >
              {showPhysics ? 'Disable Physics' : 'Enable Physics'}
            </button>
          </div>
        )}
      </div>
      
      {/* Upload Section */}
      <div className="upload-section">
        <h4>Clothing</h4>
        
        {/* File Upload */}
        <label className="upload-button">
          <input
            type="file"
            accept=".glb,.gltf"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          Upload GLB File
        </label>
        
        {/* Preset Clothing */}
        {presets.length > 0 && (
          <div className="preset-grid">
            {presets.map((preset) => (
              <button
                key={preset.id}
                className={`preset-item ${clothing?.name === preset.name ? 'active' : ''}`}
                onClick={() => onPresetSelect(preset)}
                title={preset.name}
              >
                {preset.thumbnail ? (
                  <img src={preset.thumbnail} alt={preset.name} />
                ) : (
                  <span>{preset.name.charAt(0)}</span>
                )}
              </button>
            ))}
          </div>
        )}
        
        {/* Remove Button */}
        {clothing && (
          <button className="remove-button" onClick={onRemove}>
            Remove Clothing
          </button>
        )}
      </div>
    </div>
  );
}

export default ClothingControls;
