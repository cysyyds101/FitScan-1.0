# Skill: 浏览器离线版人体识别页面开发

## 概述
为现有 React + Vite 项目交付一个完全浏览器端的离线识别页面，支持上传/拍照 → 本地模型推理 → 结果摘要展示 → 本地保存/分享/重测，全流程不依赖云端接口。

## 技术约束

### 必须遵守
1. **不使用 Tauri 或任何桌面端框架**
2. **不调用后端 API，不依赖网络服务**
3. **模型只用本地文件**：
   - `/public/models/movenet/model.json`
   - `/public/models/movenet/group1-shard1of2.bin`
   - `/public/models/movenet/group1-shard2of2.bin`
4. **识别页不显示原始复杂测量明细**（肩宽/胸围雷达图等）
5. **结果页只展示摘要**：
   - 身高（cm）
   - 推荐尺码（宽松版、修身版）
6. **数据存储使用 localStorage**（历史记录本地化）
7. **页面必须响应式**（手机/平板/桌面都正常）
8. **必须 `npm run build` 成功**

### 保持现有结构
- React + Vite 结构不变
- 优先复用已有页面和路由
- 可以重构 `src/utils/api.js` 为本地服务层
- 允许新增 util/service/hooks/components
- 不要删除用户现有业务页面

---

## 执行流程

### Day 1: 基础梳理与离线服务层

#### 1. 扫描项目结构
```bash
# 确认关键文件存在
ls frontend/src/pages/MeasurementPage.jsx
ls frontend/src/pages/ResultPage.jsx
ls frontend/src/pages/HistoryPage.jsx
ls frontend/src/utils/api.js
ls frontend/src/styles/global.css
ls frontend/public/models/movenet/
```

#### 2. 确认 API 层已本地化
检查 `src/utils/api.js`：
- `startMeasurement` → 调用本地 movenet.js
- `saveMeasurement` → 写入 localStorage
- `getHistory` → 读取 localStorage
- 无 `/api` 或外部域名请求

#### 3. 封装 localStorage 读写
```javascript
// src/utils/localStorage.js
const HISTORY_KEY = 'fitscan.measurement.history.v1'

export function readHistory() {
  const raw = localStorage.getItem(HISTORY_KEY)
  return raw ? JSON.parse(raw) : []
}

export function writeHistory(history) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
}
```

---

### Day 2: 本地模型推理闭环

#### 1. 基础 MoveNet 模型加载
```javascript
// src/utils/movenet.js
import * as tf from '@tensorflow/tfjs'

let model = null

export async function loadModel() {
  if (!model) {
    model = await tf.loadGraphModel('/models/movenet/model.json')
  }
  return model
}
```

#### 2. 增强版 MoveNet 推理（推荐）
```javascript
// src/utils/movenetEnhanced.js
import * as tf from '@tensorflow/tfjs'

class MoveNetEnhanced {
  async loadModel(preferThunder = true) {
    // 优先 Thunder 版本（精度更高），失败降级 Lightning
  }
  
  async warmup() {
    // 模型预热，避免首次推理延迟
    const dummy = tf.zeros([1, 256, 256, 3])
    await this.model.predict(dummy)
    dummy.dispose()
  }
  
  async predict(imageElement, options = {}) {
    // 预处理 → 推理 → 后处理 → 张量内存清理
  }
  
  async multiFramePredict(frames, options = {}) {
    // 多帧融合提高稳定性
  }
  
  fuseKeypoints(allKeypoints) {
    // 加权平均融合关键点
  }
  
  dispose() {
    // 释放模型资源
  }
}

export const movenet = new MoveNetEnhanced()
```

#### 3. 使用增强推理
```javascript
import { movenet } from '../utils/movenetEnhanced'

// 加载模型
await movenet.loadModel(true) // true = 优先 Thunder

// 单次推理
const keypoints = await movenet.predict(imageElement, {
  scoreThreshold: 0.3,
  flipHorizontal: false
})

// 多帧融合（更稳定）
const frames = [frame1, frame2, frame3]
const fusedKeypoints = await movenet.multiFramePredict(frames)
```

---

### Day 2.5: 图像预处理增强

#### 创建图像预处理模块
```javascript
// src/utils/imagePreprocessor.js
export class ImagePreprocessor {
  static async enhanceImage(imageDataUrl) {
    // 1. 标准化输入尺寸 (MoveNet 推荐 256x256)
    // 2. 高质量缩放
    // 3. 对比度增强 (针对暗光环境)
    // 4. 锐化处理 (增强边缘)
  }
}
```

#### 集成到 MeasurementPage
```javascript
import { enhanceImage } from '../utils/imagePreprocessor'

// 上传图片时
const enhancedImage = await enhanceImage(originalImage)
runMeasurement(enhancedImage)

// 摄像头抓帧时
const enhancedImage = await enhanceImage(imageDataUrl)
await runMeasurement(enhancedImage)
```

---

### Day 2.8: 尺码智能映射

#### 创建尺码映射器
```javascript
// src/utils/sizeMapper.js
export class SizeMapper {
  constructor(config = {}) {
    this.easingFactor = config.easingFactor || 0.15 // 放松量系数
    this.sizeChart = config.sizeChart || this.getDefaultSizeChart()
  }
  
  calculateDimensions(keypoints, originalImage) {
    // 基于关键点计算人体尺寸
    // 肩宽、胸围、腰围、臀围、身高、臂长、腿长
  }
  
  estimatePixelToCmRatio(keypoints, imageHeight) {
    // 使用人体高度作为参考估算像素到厘米比例
  }
  
  applyEasing(dimensions) {
    // 应用放松量得到穿着尺寸
  }
  
  recommendSize(dimensions, fitType = 'relaxed') {
    // 基于尺寸推荐尺码 (XS~3XL)
  }
  
  generateSizeReport(keypoints, originalImage) {
    // 生成完整的尺码推荐报告
    return {
      measurements: { height, shoulderWidth, ... },
      sizeRecommendation: 'M',        // 宽松版
      slimSizeRecommendation: 'S'     // 修身版
    }
  }
}
```

#### 默认尺码表 (中国标准)
```javascript
{
  'XS': { chest: [76, 80], waist: [60, 64], hip: [82, 86] },
  'S':  { chest: [80, 84], waist: [64, 68], hip: [86, 90] },
  'M':  { chest: [84, 88], waist: [68, 72], hip: [90, 94] },
  'L':  { chest: [88, 92], waist: [72, 76], hip: [94, 98] },
  'XL': { chest: [92, 96], waist: [76, 80], hip: [98, 102] },
  'XXL':{ chest: [96, 100], waist: [80, 84], hip: [102, 106] },
  '3XL':{ chest: [100, 106], waist: [84, 90], hip: [106, 112] }
}
```

#### 集成到测量流程
```javascript
import { movenet } from '../utils/movenetEnhanced'
import { sizeMapper } from '../utils/sizeMapper'

// 1. 加载模型
await movenet.loadModel()

// 2. 预处理图片
const enhancedImage = await enhanceImage(imageDataUrl)

// 3. 推理获取关键点
const keypoints = await movenet.predict(imageElement)

// 4. 生成尺码报告
const sizeReport = sizeMapper.generateSizeReport(keypoints, imageElement)

// 5. 返回结果
return {
  height: sizeReport.measurements.height,
  sizeRecommendation: sizeReport.sizeRecommendation,
  slimSizeRecommendation: sizeReport.slimSizeRecommendation
}
```

---

### Day 2.7: 身高估算优化

#### 创建身高估算模块
```javascript
// src/utils/heightEstimator.js
export class HeightEstimator {
  constructor(config = {}) {
    this.avgHeadToHeightRatio = 7.5    // 头身比
    this.avgHipToHeightRatio = 0.53    // 髋高身比
  }
  
  estimateHeight(keypoints, imageElement, options = {}) {
    // 主入口：根据关键点质量选择估算方法
    // 1. 全身可见 → 全身高度法
    // 2. 仅躯干可见 → 髋高推算法
    // 3. 有限关键点 → 头身比估算法
  }
  
  assessKeypointQuality(keypoints) {
    // 评估关键点质量
    // 返回：score, fullBodyVisible, torsoVisible
  }
  
  estimateFromFullBody(keypoints, imageElement, options) {
    // 全身高度法（最准确）
    // 鼻子到脚底 + 透视修正 + 姿态修正
  }
  
  estimateFromHipHeight(keypoints, imageElement) {
    // 髋高推算法
    // 髋高 / 0.53 = 身高
  }
  
  estimateFromHeadRatio(keypoints, imageElement, gender) {
    // 头身比估算法
    // 头部高度 × 7.5 = 身高
  }
  
  calculatePerspectiveFactor(keypoints, imageElement) {
    // 透视修正因子（基于肩宽/髋宽比率）
  }
  
  assessPosture(keypoints) {
    // 姿态修正因子（基于肩膀角度）
  }
  
  multiFrameEstimate(frames, imageElements, options) {
    // 多帧融合身高估算
  }
}

export const heightEstimator = new HeightEstimator()
```

#### 估算方法选择逻辑
```javascript
if (quality.fullBodyVisible) {
  // 全身可见：使用全身高度法
  heightCm = estimateFromFullBody(keypoints, imageElement)
} else if (quality.torsoVisible) {
  // 仅躯干可见：使用髋高推算法
  heightCm = estimateFromHipHeight(keypoints, imageElement)
} else {
  // 有限关键点：使用头身比估算法
  heightCm = estimateFromHeadRatio(keypoints, imageElement, gender)
}
```

#### 修正因子
| 修正类型 | 说明 | 因子 |
|----------|------|------|
| 透视修正 | 基于肩宽/髋宽比率 | 1.0 ~ 1.15 |
| 姿态修正 | 基于肩膀角度 | 1.0 ~ 1.02 |
| 脚底修正 | 脚踝到脚底 | +5% 图像高度 |
| 性别修正 | 头身比差异 | ±2% |

---

### Day 2.9: 离线服务层封装

#### 创建统一离线服务
```javascript
// src/utils/offlineService.js
export class OfflineMeasurementService {
  async init(preferThunder = true) {
    // 初始化，加载模型
  }
  
  async startMeasurement(source) {
    // 统一测量入口：图片 → 预处理 → 推理 → 尺码报告
  }
  
  assessKeypointQuality(keypoints) {
    // 评估关键点质量，判断是否有人物全身照
  }
  
  saveMeasurement(measurementData) {
    // 保存到 localStorage 历史
  }
  
  getHistory() {
    // 读取历史记录
  }
  
  deleteHistoryRecord(id) {
    // 删除单条历史
  }
  
  clearHistory() {
    // 清空历史
  }
  
  async shareMeasurement(measurementData) {
    // 分享：优先 Web Share API，降级剪贴板
  }
  
  generateShareText(measurementData) {
    // 生成分享文本
  }
}

export const offlineService = new OfflineMeasurementService()
```

#### 使用离线服务
```javascript
import { offlineService } from '../utils/offlineService'

// 初始化
await offlineService.init(true) // 优先 Thunder 模型

// 开始测量
const result = await offlineService.startMeasurement(file)
// result = {
//   measurements: { height: 172, shoulderWidth: 44, ... },
//   sizeRecommendation: 'M',
//   slimSizeRecommendation: 'S',
//   keypointQuality: { score: 0.88, ... },
//   timestamp: 1234567890
// }

// 保存历史
offlineService.saveMeasurement(result)

// 分享
await offlineService.shareMeasurement(result)

// 读取历史
const history = offlineService.getHistory()
```

---

### Day 3: 页面体验与结果页摘要化

#### 1. MeasurementPage - 简化识别页
只保留：
- 上传/拍照入口
- 识别状态（准备中/处理中/完成/失败）
- 引导文案

```jsx
// 状态机
const [status, setStatus] = useState('idle') // 'idle' | 'processing' | 'complete' | 'error'

// 引导文案
const getGuideText = () => {
  switch (status) {
    case 'idle': return '请选择上传方式，确保人物全身清晰可见'
    case 'processing': return '正在分析中，请稍候...'
    case 'complete': return '识别完成！请查看下方结果'
    case 'error': return errorMessage || '识别失败，请重试'
    default: return ''
  }
}
```

#### 2. ResultPage - 摘要卡片
```jsx
// 身高展示
<p style={{ fontSize: 'clamp(2.5rem, 8vw, 3.5rem)' }}>
  {measurementData.height}<span>cm</span>
</p>

// 尺码推荐
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)' }}>
  <div>宽松版: {measurementData.sizeRecommendation}</div>
  <div>修身版: {measurementData.slimSizeRecommendation}</div>
</div>
```

#### 3. 分享功能
```javascript
const handleShare = async () => {
  const shareText = `📏 我的身材测量结果\n身高: ${height} cm\n宽松版: ${size}\n修身版: ${slimSize}`
  
  if (navigator.share) {
    await navigator.share({ title: '我的身材测量结果', text: shareText })
  } else {
    await navigator.clipboard.writeText(shareText)
    alert('已复制到剪贴板')
  }
}
```

#### 4. HistoryPage - 简化历史
```jsx
{historyData.map(record => (
  <div key={record.id}>
    <p>📅 {record.date} {record.time}</p>
    <p>身高: {record.data.height} cm</p>
    <p>宽松版: {record.data.sizeRecommendation}</p>
    <p>修身版: {record.data.slimSizeRecommendation}</p>
  </div>
))}
```

---

### Day 4: 响应式与离线增强

#### 1. 响应式 CSS 增强
```css
/* 流体字号 */
h1 { font-size: clamp(1.8rem, 5vw, 2.5rem); }
.btn { font-size: clamp(15px, 2.5vw, 17px); }

/* 触摸友好 */
.btn, button { min-height: 48px; min-width: 48px; }

/* 断点覆盖 */
@media (max-width: 480px) { /* 手机竖屏 */ }
@media (max-width: 768px) { /* 平板 */ }
@media (min-width: 1200px) { /* 桌面 */ }
@media (min-width: 1600px) { /* 超大桌面 */ }
```

#### 2. 断网验证
- 关闭浏览器网络
- 刷新页面，确认无 API 调用
- 上传图片，确认本地推理正常
- 保存历史，确认 localStorage 写入成功

---

### Day 5: 验收与交付

#### 1. 构建验证
```bash
cd frontend
npm run build
# ✓ built in 45.78s
```

#### 2. 手测记录
| 测试项 | 操作 | 结果 |
|--------|------|------|
| 上传识别 | 选择全身照图片 | ✅ |
| 摄像头识别 | 启动摄像头→拍照 | ✅ |
| 保存历史 | 点击"保存到历史" | ✅ |
| 分享降级 | 不支持 Web Share API 时 | ✅ 剪贴板 |
| 断网可用 | 关闭网络后刷新 | ✅ |

#### 3. 交付清单
- [x] 修改文件清单（逐条）
- [x] 每个文件的改动说明
- [x] 运行步骤与验证
- [x] dist/ 目录完整（含模型文件）

---

## 关键代码模式

### 状态管理
```javascript
const [status, setStatus] = useState('idle') // 有限状态机
```

### 文件转 Base64
```javascript
const reader = new FileReader()
reader.onload = async (e) => {
  const originalImage = e.target.result
  const enhancedImage = await enhanceImage(originalImage)
  runMeasurement(enhancedImage)
}
reader.readAsDataURL(file)
```

### 图像预处理管道
```javascript
// src/utils/imagePreprocessor.js
export class ImagePreprocessor {
  // 1. 标准化输入尺寸 (MoveNet 推荐 256x256)
  // 2. 高质量缩放 (保持宽高比)
  // 3. 对比度增强 (factor=1.1)
  // 4. 锐化滤波 (amount=0.3)
}
```

### localStorage 模式
```javascript
const HISTORY_KEY = 'fitscan.measurement.history.v1'
const existing = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
existing.unshift(newRecord)
localStorage.setItem(HISTORY_KEY, JSON.stringify(existing))
```

### 响应式布局
```css
grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))
padding: clamp(16px, 4vw, 40px)
```

---

## 文件清单

| 文件 | 说明 |
|------|------|
| `src/utils/imagePreprocessor.js` | 图像预处理管道：标准化尺寸、对比度增强、锐化滤波 |
| `src/utils/movenetEnhanced.js` | 增强版 MoveNet 推理：模型预热、多帧融合、内存管理 |
| `src/utils/heightEstimator.js` | 身高估算优化：多方法选择、透视/姿态修正、多帧融合 |
| `src/utils/sizeMapper.js` | 尺码智能映射器：关键点→尺寸→尺码推荐 |
| `src/utils/offlineService.js` | 离线服务层封装：统一测量接口、历史管理、分享 |
| `src/pages/MeasurementPage.jsx` | 识别页：上传/拍照、状态引导、图片显示 |
| `src/pages/ResultPage.jsx` | 结果页：身高+尺码摘要卡片、保存/分享/重测按钮 |
| `src/pages/HistoryPage.jsx` | 历史页：简化摘要记录列表 |
| `src/styles/global.css` | 响应式样式：流体排版、触摸友好、多断点适配 |

---

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 模型加载失败 | 确认 `/public/models/movenet/` 路径正确 |
| 摄像头无法访问 | 检查浏览器权限，确认 HTTPS/localhost |
| 分享功能不可用 | 降级到剪贴板复制 |
| 页面过小 | 使用 clamp() 和 viewport meta |
| build 失败 | 检查 import 路径，清除 node_modules 重装 |

---

## 扩展建议

1. **PWA 缓存**：添加 service worker 缓存静态资源和模型文件
2. **IndexedDB**：替代 localStorage 支持更大规模历史数据
3. **Worker 隔离**：将模型推理放入 Web Worker 避免阻塞 UI
4. **多语言**：提取文案为 i18n 资源文件
5. **图像预处理增强**：已实现对比度增强和锐化滤波，可进一步添加自动曝光、色彩校正
6. **模型推理增强**：已实现模型预热、多帧融合、内存管理，可添加 Tensor 可视化
7. **身高估算增强**：已实现多方法选择、透视/姿态修正，可添加地面检测、深度估计
8. **尺码映射增强**：已实现基于关键点的尺寸计算，可添加个性化体型分析、品牌尺码适配
9. **离线服务增强**：已实现统一测量接口，可添加批量处理、离线同步、数据导出
