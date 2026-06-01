import { useState, useCallback } from 'react';
import './ClothingControls.css';

/**
 * 服装控制面板组件
 * 用于控制服装位置、旋转、缩放和物理效果
 */
export function ClothingControls({
  adjustment,
  physicsConfig,
  showPhysics,
  presets = [],
  clothing,
  onUpload,
  onPresetSelect,
  onRemove,
  onAdjustmentChange,
  onPhysicsChange,
  onTogglePhysics,
  onReset
}) {
  const [activeTab, setActiveTab] = useState('position');
  
  // 处理文件输入变化
  const handleFileChange = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
    }
  }, [onUpload]);
  
  // 处理位置滑块变化
  const handlePositionChange = useCallback((axis, value) => {
    const numValue = parseFloat(value);
    onAdjustmentChange({
      ...adjustment,
      positionOffset: {
        ...adjustment.positionOffset,
        [axis]: numValue
      }
    });
  }, [adjustment, onAdjustmentChange]);
  
  // 处理旋转滑块变化
  const handleRotationChange = useCallback((axis, value) => {
    const numValue = parseFloat(value);
    onAdjustmentChange({
      ...adjustment,
      rotationOffset: {
        ...adjustment.rotationOffset,
        [axis]: numValue
      }
    });
  }, [adjustment, onAdjustmentChange]);
  
  // 处理缩放滑块变化
  const handleScaleChange = useCallback((value) => {
    const numValue = parseFloat(value);
    onAdjustmentChange({
      ...adjustment,
      scale: numValue
    });
  }, [adjustment, onAdjustmentChange]);
  
  // 处理重置
  const handleReset = useCallback(() => {
    if (onReset) {
      onReset();
    }
  }, [onReset]);
  
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
            物理
          </button>
        )}
      </div>
      
      {/* Tab 内容 */}
      <div className="controls-content">
        {/* 位置 Tab */}
        {activeTab === 'position' && (
          <div className="control-group">
            <div className="control-header">
              <h4>位置偏移</h4>
              <button className="reset-btn" onClick={handleReset} title="重置">↺</button>
            </div>
            
            <div className="slider-control">
              <label>X轴 (左右)</label>
              <input
                type="range"
                min="-0.5"
                max="0.5"
                step="0.01"
                value={adjustment?.positionOffset?.x ?? 0}
                onChange={(e) => handlePositionChange('x', e.target.value)}
              />
              <span>{(adjustment?.positionOffset?.x ?? 0).toFixed(2)}</span>
            </div>
            
            <div className="slider-control">
              <label>Y轴 (上下)</label>
              <input
                type="range"
                min="-0.5"
                max="0.5"
                step="0.01"
                value={adjustment?.positionOffset?.y ?? 0}
                onChange={(e) => handlePositionChange('y', e.target.value)}
              />
              <span>{(adjustment?.positionOffset?.y ?? 0).toFixed(2)}</span>
            </div>
            
            <div className="slider-control">
              <label>Z轴 (前后)</label>
              <input
                type="range"
                min="-0.5"
                max="0.5"
                step="0.01"
                value={adjustment?.positionOffset?.z ?? 0}
                onChange={(e) => handlePositionChange('z', e.target.value)}
              />
              <span>{(adjustment?.positionOffset?.z ?? 0).toFixed(2)}</span>
            </div>
          </div>
        )}
        
        {/* 旋转 Tab */}
        {activeTab === 'rotation' && (
          <div className="control-group">
            <div className="control-header">
              <h4>旋转角度</h4>
              <button className="reset-btn" onClick={handleReset} title="重置">↺</button>
            </div>
            
            <div className="slider-control">
              <label>X轴 (俯仰)</label>
              <input
                type="range"
                min="-90"
                max="90"
                step="1"
                value={adjustment?.rotationOffset?.x ?? 0}
                onChange={(e) => handleRotationChange('x', e.target.value)}
              />
              <span>{(adjustment?.rotationOffset?.x ?? 0)}°</span>
            </div>
            
            <div className="slider-control">
              <label>Y轴 (水平)</label>
              <input
                type="range"
                min="-180"
                max="180"
                step="1"
                value={adjustment?.rotationOffset?.y ?? 0}
                onChange={(e) => handleRotationChange('y', e.target.value)}
              />
              <span>{(adjustment?.rotationOffset?.y ?? 0)}°</span>
            </div>
            
            <div className="slider-control">
              <label>Z轴 (倾斜)</label>
              <input
                type="range"
                min="-90"
                max="90"
                step="1"
                value={adjustment?.rotationOffset?.z ?? 0}
                onChange={(e) => handleRotationChange('z', e.target.value)}
              />
              <span>{(adjustment?.rotationOffset?.z ?? 0)}°</span>
            </div>
          </div>
        )}
        
        {/* 缩放 Tab */}
        {activeTab === 'scale' && (
          <div className="control-group">
            <div className="control-header">
              <h4>服装大小</h4>
              <button className="reset-btn" onClick={handleReset} title="重置">↺</button>
            </div>
            
            <div className="slider-control">
              <label>缩放比例</label>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.01"
                value={adjustment?.scale ?? 1}
                onChange={(e) => handleScaleChange(e.target.value)}
              />
              <span>{(adjustment?.scale ?? 1).toFixed(2)}x</span>
            </div>
          </div>
        )}
        
        {/* 物理效果 Tab */}
        {activeTab === 'physics' && (
          <div className="control-group">
            <h4>布料物理效果</h4>
            <p className="physics-hint">布料物理需要浏览器支持 WebGPU</p>
            
            <div className="slider-control">
              <label>硬度</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={physicsConfig?.stiffness ?? 0.3}
                onChange={(e) => onPhysicsChange({ ...physicsConfig, stiffness: parseFloat(e.target.value) })}
              />
              <span>{(physicsConfig?.stiffness ?? 0.3).toFixed(2)}</span>
            </div>
            
            <div className="slider-control">
              <label>阻尼</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={physicsConfig?.dampening ?? 0.5}
                onChange={(e) => onPhysicsChange({ ...physicsConfig, dampening: parseFloat(e.target.value) })}
              />
              <span>{(physicsConfig?.dampening ?? 0.5).toFixed(2)}</span>
            </div>
            
            <div className="slider-control">
              <label>风力 X</label>
              <input
                type="range"
                min="-5"
                max="5"
                step="0.1"
                value={physicsConfig?.wind?.x ?? 0}
                onChange={(e) => onPhysicsChange({ 
                  ...physicsConfig, 
                  wind: { ...physicsConfig.wind, x: parseFloat(e.target.value) }
                })}
              />
              <span>{(physicsConfig?.wind?.x ?? 0).toFixed(1)}</span>
            </div>
            
            <div className="slider-control">
              <label>风力 Z</label>
              <input
                type="range"
                min="-5"
                max="5"
                step="0.1"
                value={physicsConfig?.wind?.z ?? 1}
                onChange={(e) => onPhysicsChange({ 
                  ...physicsConfig, 
                  wind: { ...physicsConfig.wind, z: parseFloat(e.target.value) }
                })}
              />
              <span>{(physicsConfig?.wind?.z ?? 1).toFixed(1)}</span>
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
        <h4>选择服装</h4>
        
        {/* 预设服装 */}
        {presets.length > 0 && (
          <div className="preset-grid">
            {presets.map((preset) => (
              <button
                key={preset.id}
                className={`preset-item ${clothing?.id === preset.id ? 'active' : ''}`}
                onClick={() => onPresetSelect(preset)}
                title={preset.name}
              >
                <span 
                  className="preset-color"
                  style={{ backgroundColor: preset.color }}
                >
                  {preset.name.charAt(0)}
                </span>
              </button>
            ))}
          </div>
        )}
        
        {/* 当前服装名称 */}
        {clothing && (
          <p className="current-clothing">{clothing.name}</p>
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
