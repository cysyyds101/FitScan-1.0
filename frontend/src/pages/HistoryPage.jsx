import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { RadarChart } from '../components/Charts'

const HISTORY_KEY = 'fitscan.measurement.history.v1'

function readHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch (error) {
    console.warn('读取历史记录失败:', error)
    return []
  }
}

function writeHistory(history) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
}

// 统计数据计算
function calculateStats(historyData) {
  if (historyData.length === 0) return null
  
  const latest = historyData[0]?.data || {}
  const avgHeight = historyData.reduce((sum, r) => sum + (r.data.height || 0), 0) / historyData.length
  const measurements = historyData.length
  
  return {
    latest,
    avgHeight: Math.round(avgHeight * 10) / 10,
    measurements,
    date: historyData[0]?.date || ''
  }
}

// 雷达图数据转换
function getRadarData(measurement) {
  return {
    indicators: [
      { name: '身高', max: 200 },
      { name: '肩宽', max: 60 },
      { name: '胸围', max: 130 },
      { name: '腰围', max: 120 },
      { name: '臀围', max: 130 },
      { name: '臂长', max: 100 }
    ],
    values: [
      measurement.height || 170,
      measurement.shoulderWidth || 45,
      measurement.chest || 95,
      measurement.waist || 80,
      measurement.hip || 95,
      measurement.armLength || 70
    ]
  }
}

const HistoryPage = () => {
  const [historyData, setHistoryData] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedRecord, setSelectedRecord] = useState(null)
  const [showStats, setShowStats] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true)
        await new Promise(resolve => setTimeout(resolve, 200))
        const data = readHistory()
        setHistoryData(data)
        if (data.length > 0) {
          setSelectedRecord(data[0])
        }
      } catch (error) {
        console.error('获取历史记录失败:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [])

  const deleteRecord = (id, e) => {
    e.stopPropagation()
    if (window.confirm('确定要删除这条记录吗？')) {
      const updated = historyData.filter(record => record.id !== id)
      setHistoryData(updated)
      writeHistory(updated)
      if (selectedRecord?.id === id) {
        setSelectedRecord(updated[0] || null)
      }
    }
  }

  const clearAll = () => {
    if (window.confirm('确定要清空所有历史记录吗？此操作不可恢复。')) {
      setHistoryData([])
      writeHistory([])
      setSelectedRecord(null)
    }
  }

  const exportData = () => {
    const dataStr = JSON.stringify(historyData, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `fitscan-history-${new Date().toISOString().slice(0,10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="loading" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div className="loading-spinner"></div>
      </div>
    )
  }

  const stats = calculateStats(historyData)

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '24px 16px' }}>
      {/* 标题栏 */}
      <motion.div 
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: 0 }}>历史记录</h1>
        <div style={{ display: 'flex', gap: '12px' }}>
          {historyData.length > 0 && (
            <>
              <button 
                onClick={() => setShowStats(!showStats)}
                style={{ 
                  background: showStats ? '#4a90d9' : 'white', 
                  border: '1px solid #4a90d9', 
                  color: showStats ? 'white' : '#4a90d9',
                  padding: '8px 16px', 
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                {showStats ? '收起统计' : '查看统计'}
              </button>
              <button 
                onClick={exportData}
                style={{ 
                  background: 'white', 
                  border: '1px solid #4a90d9', 
                  color: '#4a90d9',
                  padding: '8px 16px', 
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                导出数据
              </button>
              <button 
                onClick={clearAll}
                style={{ 
                  background: 'white', 
                  border: '1px solid #f44336', 
                  color: '#f44336',
                  padding: '8px 16px', 
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                清空全部
              </button>
            </>
          )}
        </div>
      </motion.div>

      {/* 统计面板 */}
      {showStats && stats && (
        <motion.div 
          className="card"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          style={{ marginBottom: '24px', padding: '24px' }}
        >
          <h3 style={{ marginTop: 0, marginBottom: '16px' }}>数据统计</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
            <div style={{ textAlign: 'center', padding: '16px', background: '#f5f5f5', borderRadius: '12px' }}>
              <p style={{ color: '#888', fontSize: '0.85rem', marginBottom: '8px' }}>记录总数</p>
              <p style={{ fontSize: '2rem', fontWeight: 700, color: '#4a90d9', margin: 0 }}>{stats.measurements}</p>
            </div>
            <div style={{ textAlign: 'center', padding: '16px', background: '#f5f5f5', borderRadius: '12px' }}>
              <p style={{ color: '#888', fontSize: '0.85rem', marginBottom: '8px' }}>最新身高</p>
              <p style={{ fontSize: '2rem', fontWeight: 700, color: '#e74c3c', margin: 0 }}>{stats.latest.height} <span style={{ fontSize: '0.8rem', color: '#888' }}>cm</span></p>
            </div>
            <div style={{ textAlign: 'center', padding: '16px', background: '#f5f5f5', borderRadius: '12px' }}>
              <p style={{ color: '#888', fontSize: '0.85rem', marginBottom: '8px' }}>平均身高</p>
              <p style={{ fontSize: '2rem', fontWeight: 700, color: '#9b59b6', margin: 0 }}>{stats.avgHeight} <span style={{ fontSize: '0.8rem', color: '#888' }}>cm</span></p>
            </div>
            <div style={{ textAlign: 'center', padding: '16px', background: '#f5f5f5', borderRadius: '12px' }}>
              <p style={{ color: '#888', fontSize: '0.85rem', marginBottom: '8px' }}>宽松码推荐</p>
              <p style={{ fontSize: '2rem', fontWeight: 700, color: '#2ecc71', margin: 0 }}>{stats.latest.sizeRecommendation || 'M'}</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* 空状态 */}
      {historyData.length === 0 ? (
        <motion.div 
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          style={{ textAlign: 'center', padding: '48px 24px' }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📋</div>
          <h2 style={{ marginBottom: '12px', fontSize: '1.3rem' }}>暂无历史记录</h2>
          <p style={{ marginBottom: '24px', color: '#666' }}>您还没有进行过测量，请先开始测量</p>
          <button 
            className="btn btn-primary"
            onClick={() => navigate('/measurement')}
            style={{ padding: '14px 32px' }}
          >
            开始测量
          </button>
        </motion.div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          {/* 左侧：记录列表 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {historyData.map((record, index) => (
              <motion.div 
                key={record.id}
                className="card"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                onClick={() => setSelectedRecord(record)}
                style={{ 
                  padding: '16px',
                  cursor: 'pointer',
                  border: selectedRecord?.id === record.id ? '2px solid #4a90d9' : '2px solid transparent',
                  background: selectedRecord?.id === record.id ? '#f0f7ff' : 'white'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{ fontWeight: 600, fontSize: '1rem' }}>测量记录</span>
                      {index === 0 && <span style={{ background: '#4a90d9', color: 'white', padding: '2px 8px', borderRadius: '10px', fontSize: '0.75rem' }}>最新</span>}
                    </div>
                    <p style={{ color: '#888', fontSize: '0.85rem', marginBottom: '8px' }}>
                      📅 {record.date} {record.time}
                    </p>
                  </div>
                  <button 
                    onClick={(e) => deleteRecord(record.id, e)}
                    style={{ 
                      background: 'none', 
                      border: 'none', 
                      color: '#f44336',
                      cursor: 'pointer',
                      fontSize: '1.2rem',
                      padding: '4px 8px'
                    }}
                    title="删除"
                  >
                    ×
                  </button>
                </div>
                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                  <div>
                    <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '2px' }}>身高</p>
                    <p style={{ fontWeight: 600 }}>{record.data.height} cm</p>
                  </div>
                  <div>
                    <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '2px' }}>宽松版</p>
                    <p style={{ fontWeight: 600, color: '#4a90d9' }}>{record.data.sizeRecommendation || 'M'}</p>
                  </div>
                  <div>
                    <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '2px' }}>修身版</p>
                    <p style={{ fontWeight: 600, color: '#9b59b6' }}>{record.data.slimSizeRecommendation || 'M'}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* 右侧：详情/雷达图 */}
          <div>
            {selectedRecord ? (
              <motion.div 
                className="card"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                style={{ padding: '24px' }}
              >
                <h3 style={{ marginTop: 0, marginBottom: '16px' }}>体型数据详情</h3>
                <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '16px' }}>
                  {selectedRecord.date} {selectedRecord.time}
                </p>
                
                {/* 雷达图 */}
                <div style={{ height: '280px', marginBottom: '20px' }}>
                  <RadarChart data={getRadarData(selectedRecord.data)} />
                </div>
                
                {/* 详细数据 */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                  <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '4px' }}>身高</p>
                    <p style={{ fontWeight: 600, fontSize: '1.1rem' }}>{selectedRecord.data.height} cm</p>
                  </div>
                  <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '4px' }}>肩宽</p>
                    <p style={{ fontWeight: 600, fontSize: '1.1rem' }}>{selectedRecord.data.shoulderWidth || '-'} cm</p>
                  </div>
                  <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '4px' }}>胸围</p>
                    <p style={{ fontWeight: 600, fontSize: '1.1rem' }}>{selectedRecord.data.chest || '-'} cm</p>
                  </div>
                  <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '4px' }}>腰围</p>
                    <p style={{ fontWeight: 600, fontSize: '1.1rem' }}>{selectedRecord.data.waist || '-'} cm</p>
                  </div>
                  <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '4px' }}>臀围</p>
                    <p style={{ fontWeight: 600, fontSize: '1.1rem' }}>{selectedRecord.data.hip || '-'} cm</p>
                  </div>
                  <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '4px' }}>臂长</p>
                    <p style={{ fontWeight: 600, fontSize: '1.1rem' }}>{selectedRecord.data.armLength || '-'} cm</p>
                  </div>
                </div>
                
                <button 
                  className="btn btn-primary"
                  onClick={() => navigate('/virtual-tryon')}
                  style={{ width: '100%', marginTop: '20px' }}
                >
                  去虚拟换衣
                </button>
              </motion.div>
            ) : (
              <div className="card" style={{ textAlign: 'center', padding: '48px 24px', color: '#888' }}>
                点击左侧记录查看详情
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default HistoryPage
