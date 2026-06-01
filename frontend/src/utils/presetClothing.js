/**
 * Preset Clothing Data
 * Contains predefined clothing options with metadata
 */

export const PRESET_CLOTHING = [
  {
    id: 'tshirt-red',
    name: '红色T恤',
    nameEn: 'Red T-Shirt',
    description: '经典红色棉质T恤',
    price: 0,
    url: '/models/clothing/tshirt_red.glb',
    thumbnail: null,
    category: 'top',
    color: '#e74c3c',
    tags: ['casual', 'summer', 'basic']
  },
  {
    id: 'hoodie-blue',
    name: '蓝色卫衣',
    nameEn: 'Blue Hoodie',
    description: '舒适蓝色连帽卫衣',
    price: 0,
    url: '/models/clothing/hoodie_blue.glb',
    thumbnail: null,
    category: 'top',
    color: '#3498db',
    tags: ['casual', 'winter', 'hoodie']
  },
  {
    id: 'dress-purple',
    name: '紫色连衣裙',
    nameEn: 'Purple Dress',
    description: '优雅紫色连衣裙',
    price: 0,
    url: '/models/clothing/dress_purple.glb',
    thumbnail: null,
    category: 'dress',
    color: '#9b59b6',
    tags: ['elegant', 'summer', 'formal']
  }
];

/**
 * Get clothing by category
 */
export function getClothingByCategory(category) {
  return PRESET_CLOTHING.filter(item => item.category === category);
}

/**
 * Get clothing by ID
 */
export function getClothingById(id) {
  return PRESET_CLOTHING.find(item => item.id === id);
}

/**
 * Get all categories
 */
export function getCategories() {
  const categories = [...new Set(PRESET_CLOTHING.map(item => item.category))];
  return categories;
}

/**
 * Get clothing by tag
 */
export function getClothingByTag(tag) {
  return PRESET_CLOTHING.filter(item => item.tags.includes(tag));
}

/**
 * SVG thumbnail components for preset clothing
 */
export const ClothingThumbnails = {
  'tshirt-red': `
    <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <path d="M16 20 L24 12 L32 16 L40 12 L48 20 L44 24 L40 22 L40 52 L24 52 L24 22 L20 24 L16 20 Z" 
            fill="#e74c3c" stroke="#c0392b" stroke-width="1"/>
    </svg>
  `,
  'hoodie-blue': `
    <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 22 L22 14 L32 18 L42 14 L50 22 L46 26 L42 24 L42 54 L22 54 L22 24 L18 26 L14 22 Z" 
            fill="#3498db" stroke="#2980b9" stroke-width="1"/>
      <ellipse cx="32" cy="16" rx="8" ry="4" fill="#2980b9"/>
    </svg>
  `,
  'dress-purple': `
    <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <path d="M26 14 L38 14 L40 24 L48 54 L16 54 L24 24 L26 14 Z" 
            fill="#9b59b6" stroke="#8e44ad" stroke-width="1"/>
    </svg>
  `
};

/**
 * Generate SVG data URL for a thumbnail
 */
export function getThumbnailDataUrl(id, color = '#666') {
  const svg = ClothingThumbnails[id];
  if (svg) {
    return `data:image/svg+xml,${encodeURIComponent(svg)}`;
  }
  return null;
}

export default PRESET_CLOTHING;
