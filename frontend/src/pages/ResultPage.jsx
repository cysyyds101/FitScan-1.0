import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Radar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'

// 注册Chart.js组件
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
)

const ResultPage = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const [measurementData, setMeasurementData] = useState(null)

  // 从路由状态中获取测量数据
  useEffect(() => {
    if (location.state && location.state.measurementData) {
      setMeasurementData(location.state.measurementData)
    } else {
      // 如果没有数据，重定向到测量页面
      navigate('/measurement')
    }
  }, [location.state, navigate])

  // 计算雷达图数据
  const getRadarData = () => {
    if (!measurementData) return null

    return {
      labels: ['身高', '肩宽', '胸围', '腰围', '臀围'],
      datasets: [
        {
          label: '您的体型',
          data: [
            measurementData.height / 2, // 归一化处理
            measurementData.shoulderWidth * 2,
            measurementData.chest / 2,
            measurementData.waist / 2,
            measurementData.hip / 2
          ],
          backgroundColor: 'rgba(76, 175, 80, 0.2)',
          borderColor: 'rgba(76, 175, 80, 1)',
          pointBackgroundColor: 'rgba(76, 175, 80, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(76, 175, 80, 1)'
        }
      ]
    }
  }

  // 雷达图配置
  const radarOptions = {
    scales: {
      r: {
        angleLines: {
          display: true
        },
        suggestedMin: 0,
        suggestedMax: 100
      }
    }
  }

  if (!measurementData) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  return (
    <div className="result-page" style={{ margin: '40px 0' }}>
      <motion.h1 
        style={{ textAlign: 'center', marginBottom: '40px' }}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        测量结果
      </motion.h1>

      {/* 尺码推荐卡片 */}
      <motion.div 
        className="card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        style={{ marginBottom: '40px' }}
      >
        <h2 style={{ marginBottom: '20px' }}>尺码推荐</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <h3 style={{ marginBottom: '10px' }}>宽松版</h3>
            <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#4CAF50' }}>
              {measurementData.sizeRecommendation}
            </p>
          </div>
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <h3 style={{ marginBottom: '10px' }}>修身版</h3>
            <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#4CAF50' }}>
              {measurementData.slimSizeRecommendation}
            </p>
          </div>
        </div>
      </motion.div>

      {/* 测量数据和体型分析 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px' }} className="grid grid-cols-2">
        {/* 测量数据 */}
        <motion.div 
          className="card"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 style={{ marginBottom: '30px' }}>测量数据</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {[
              { label: '肩宽', value: measurementData.shoulderWidth, unit: 'cm' },
              { label: '臂长', value: measurementData.armLength, unit: 'cm' },
              { label: '腿长', value: measurementData.legLength, unit: 'cm' },
              { label: '身高', value: measurementData.height, unit: 'cm' },
              { label: '胸围', value: measurementData.chest, unit: 'cm' },
              { label: '腰围', value: measurementData.waist, unit: 'cm' },
              { label: '臀围', value: measurementData.hip, unit: 'cm' }
            ].map((item, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.3 + index * 0.1 }}
                style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  padding: '12px', 
                  backgroundColor: '#f8f9fa', 
                  borderRadius: '6px' 
                }}
              >
                <span style={{ color: '#555' }}>{item.label}</span>
                <span style={{ fontWeight: 'bold' }}>{item.value.toFixed(1)} {item.unit}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* 体型分析雷达图 */}
        <motion.div 
          className="card"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <h2 style={{ marginBottom: '30px' }}>体型分析</h2>
          <div style={{ height: '300px' }}>
            <Radar data={getRadarData()} options={radarOptions} />
          </div>
        </motion.div>
      </div>

      {/* 操作按钮 */}
      <motion.div 
        style={{ marginTop: '40px', textAlign: 'center' }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <button 
          className="btn btn-primary" 
          onClick={() => navigate('/measurement')}
          style={{ marginRight: '16px' }}
        >
          重新测量
        </button>
        <button 
          className="btn btn-secondary" 
          onClick={() => navigate('/history')}
          style={{ marginRight: '16px' }}
        >
          查看历史记录
        </button>
        <button 
          className="btn btn-secondary" 
          onClick={() => navigate('/')}
        >
          返回首页
        </button>
      </motion.div>
    </div>
  )
}

export default ResultPage