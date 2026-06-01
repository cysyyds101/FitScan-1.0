/**
 * 预设服装数据
 */

export const PRESET_CLOTHING = [
  {
    id: 'tshirt-red',
    name: '红色T恤',
    description: '经典红色棉质T恤',
    color: '#e74c3c',
    category: 'top'
  },
  {
    id: 'hoodie-blue',
    name: '蓝色卫衣',
    description: '舒适蓝色连帽卫衣',
    color: '#3498db',
    category: 'top'
  },
  {
    id: 'dress-purple',
    name: '紫色连衣裙',
    description: '优雅紫色连衣裙',
    color: '#9b59b6',
    category: 'dress'
  }
];

/**
 * 获取所有预设服装
 */
export function getAllPresets() {
  return PRESET_CLOTHING;
}

/**
 * 根据分类获取服装
 */
export function getByCategory(category) {
  return PRESET_CLOTHING.filter(item => item.category === category);
}

/**
 * 根据ID获取服装
 */
export function getById(id) {
  return PRESET_CLOTHING.find(item => item.id === id);
}

export default PRESET_CLOTHING;
