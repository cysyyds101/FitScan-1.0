import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 模拟数据
const mockMeasurementData = {
  shoulderWidth: 42.5,
  armLength: 68.3,
  legLength: 95.7,
  height: 175.2,
  chest: 92.1,
  waist: 76.5,
  hip: 94.3,
  sizeRecommendation: 'M (宽松版)',
  slimSizeRecommendation: 'M (修身版)'
}

const mockHistoryData = [
  {
    id: 1,
    date: '2026-04-12',
    time: '14:30',
    data: mockMeasurementData
  },
  {
    id: 2,
    date: '2026-04-10',
    time: '10:15',
    data: {
      ...mockMeasurementData,
      shoulderWidth: 43.0,
      chest: 93.5,
      sizeRecommendation: 'L (宽松版)',
      slimSizeRecommendation: 'M (修身版)'
    }
  },
  {
    id: 3,
    date: '2026-04-05',
    time: '16:45',
    data: {
      ...mockMeasurementData,
      height: 176.0,
      legLength: 96.5,
      sizeRecommendation: 'M (宽松版)',
      slimSizeRecommendation: 'M (修身版)'
    }
  }
]

// API方法
const apiMethods = {
  // 开始测量
  startMeasurement: async () => {
    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 3000))
    return {
      data: mockMeasurementData
    }
  },

  // 检测参照物
  detectReference: async (referenceType) => {
    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 2000))
    return {
      data: {
        detected: true,
        referenceType: referenceType || 'A4',
        calibrationSuccess: true
      }
    }
  },

  // 获取历史记录
  getHistory: async () => {
    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 1000))
    return {
      data: mockHistoryData
    }
  },

  // 保存测量结果
  saveMeasurement: async (data) => {
    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 1000))
    return {
      data: {
        success: true,
        id: Date.now()
      }
    }
  }
}

// 导出API方法
export default apiMethods