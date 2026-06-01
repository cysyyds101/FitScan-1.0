import { useState, useCallback } from 'react';
import './ClothingControls.css';

/**
 * 服装控制面板组件
 * 用于控制服装位置、旋转、缩放和物理效果
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
  
  // 处理文件输入变化
  const handleFileChange = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
    }
  }, [onUpload]);
  
  // 处理滑块变化
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
  
  // 处理物理向量滑块
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
      {/* Tab 导航 */}
      <div className="controls-tabs">
        <button 
          className={activeTab === 'position' ? 'active' : ''}
          onClick={() => setActiveTab('position')}
        >
          位置
        </button>
        <button 
          className={activeTab === 'rotation' ? 'active' : ''}
          onClick={() => setActiveTab('rotation')}
        >
          旋转
        </button>
        <button 
          className={activeTab === 'scale' ? 'active' : ''}
          onClick={() => setActiveTab('scale')}
        >
          大小
        </button>
        {showPhysics && (
          <button 
            className={activeTab === 'physics' ? 'active' : ''}
            onClick={() => setActiveTab('physics')}
          >
            物理效果
          </button>
        )}
      </div>
      
      {/* Tab 内容 */}
      <div className="controls-content">
        {/* 位置 Tab */}
        {activeTab === 'position' && (
          <div className="control-group">
            <h4>位置偏移</h4>
            
            <div className="slider-control">
              <label>X轴 (左右)</label>
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
              <label>Y轴 (上下)</label>
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
              <label>Z轴 (前后)</label>
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
        
        {/* 旋转 Tab */}
        {activeTab === 'rotation' && (
          <div className="control-group">
            <h4>旋转角度</h4>
            
            <div className="slider-control">
              <label>X轴 (俯仰)</label>
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
              <label>Y轴 (水平)</label>
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
              <label>Z轴 (倾斜)</label>
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
        
        {/* 缩放 Tab */}
        {activeTab === 'scale' && (
          <div className="control-group">
            <h4>服装大小</h4>
            
            <div className="slider-control">
              <label>缩放比例</label>
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
        
        {/* 物理效果 Tab */}
        {activeTab === 'physics' && (
          <div className="control-group">
            <h4>布料物理效果</h4>
            
            <div className="slider-control">
              <label>硬度</label>
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
              <label>阻尼</label>
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
              <label>风力 X</label>
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
              <label>风力 Z</label>
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
              {showPhysics ? '关闭物理效果' : '开启物理效果'}
            </button>
          </div>
        )}
      </div>
      
      {/* 上传区域 */}
      <div className="upload-section">
        <h4>服装选择</h4>
        
        {/* 文件上传 */}
        <label className="upload-button">
          <input
            type="file"
            accept=".glb,.gltf"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          上传 GLB 文件
        </label>
        
        {/* 预设服装 */}
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
        
        {/* 移除按钮 */}
        {clothing && (
          <button className="remove-button" onClick={onRemove}>
            移除服装
          </button>
        )}
      </div>
    </div>
  );
}

export default ClothingControls;
