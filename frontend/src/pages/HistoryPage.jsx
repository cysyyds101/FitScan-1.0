import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../utils/api'

const HistoryPage = () => {
  const [historyData, setHistoryData] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedRecord, setSelectedRecord] = useState(null)
  const navigate = useNavigate()

  // 获取历史记录
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true)
        const response = await api.getHistory()
        setHistoryData(response.data)
      } catch (error) {
        console.error('Error fetching history:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [])

  // 查看记录详情
  const viewRecord = (record) => {
    setSelectedRecord(record)
  }

  // 关闭详情
  const closeDetails = () => {
    setSelectedRecord(null)
  }

  // 模拟删除记录
  const deleteRecord = (id) => {
    if (window.confirm('确定要删除这条记录吗？')) {
      setHistoryData(historyData.filter(record => record.id !== id))
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  return (
    <div className="history-page" style={{ margin: '40px 0' }}>
      <motion.h1 
        style={{ textAlign: 'center', marginBottom: '40px' }}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        历史测量记录
      </motion.h1>

      {historyData.length === 0 ? (
        <motion.div 
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          style={{ textAlign: 'center', padding: '60px' }}
        >
          <h2 style={{ marginBottom: '20px' }}>暂无历史记录</h2>
          <p style={{ marginBottom: '30px', color: '#666' }}>您还没有进行过测量，请先开始测量</p>
          <button 
            className="btn btn-primary"
            onClick={() => navigate('/measurement')}
          >
            开始测量
          </button>
        </motion.div>
      ) : (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {historyData.map((record, index) => (
            <motion.div 
              key={record.id}
              className="card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              style={{ marginBottom: '20px' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3>测量记录 #{record.id}</h3>
                  <p style={{ color: '#666' }}>{record.date} {record.time}</p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => viewRecord(record)}
                    style={{ padding: '8px 16px', fontSize: '14px' }}
                  >
                    查看详情
                  </button>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => deleteRecord(record.id)}
                    style={{ 
                      padding: '8px 16px', 
                      fontSize: '14px',
                      backgroundColor: '#f44336',
                      color: 'white'
                    }}
                  >
                    删除
                  </button>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
                <div style={{ textAlign: 'center', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                  <p style={{ fontSize: '14px', color: '#666', marginBottom: '4px' }}>肩宽</p>
                  <p style={{ fontWeight: 'bold' }}>{record.data.shoulderWidth.toFixed(1)} cm</p>
                </div>
                <div style={{ textAlign: 'center', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                  <p style={{ fontSize: '14px', color: '#666', marginBottom: '4px' }}>身高</p>
                  <p style={{ fontWeight: 'bold' }}>{record.data.height.toFixed(1)} cm</p>
                </div>
                <div style={{ textAlign: 'center', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                  <p style={{ fontSize: '14px', color: '#666', marginBottom: '4px' }}>胸围</p>
                  <p style={{ fontWeight: 'bold' }}>{record.data.chest.toFixed(1)} cm</p>
                </div>
                <div style={{ textAlign: 'center', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                  <p style={{ fontSize: '14px', color: '#666', marginBottom: '4px' }}>推荐尺码</p>
                  <p style={{ fontWeight: 'bold' }}>{record.data.sizeRecommendation}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* 记录详情模态框 */}
      {selectedRecord && (
        <motion.div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <motion.div 
            className="card"
            style={{ 
              width: '90%', 
              maxWidth: '600px', 
              maxHeight: '80vh', 
              overflowY: 'auto'
            }}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2>测量详情</h2>
              <button 
                onClick={closeDetails}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  fontSize: '24px', 
                  cursor: 'pointer',
                  color: '#666'
                }}
              >
                ×
              </button>
            </div>
            <p style={{ marginBottom: '20px', color: '#666' }}>
              测量时间：{selectedRecord.date} {selectedRecord.time}
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '30px' }}>
              {[
                { label: '肩宽', value: selectedRecord.data.shoulderWidth, unit: 'cm' },
                { label: '臂长', value: selectedRecord.data.armLength, unit: 'cm' },
                { label: '腿长', value: selectedRecord.data.legLength, unit: 'cm' },
                { label: '身高', value: selectedRecord.data.height, unit: 'cm' },
                { label: '胸围', value: selectedRecord.data.chest, unit: 'cm' },
                { label: '腰围', value: selectedRecord.data.waist, unit: 'cm' },
                { label: '臀围', value: selectedRecord.data.hip, unit: 'cm' },
                { label: '宽松版推荐', value: selectedRecord.data.sizeRecommendation, unit: '' },
                { label: '修身版推荐', value: selectedRecord.data.slimSizeRecommendation, unit: '' }
              ].map((item, index) => (
                <div key={index} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #eee' }}>
                  <span style={{ color: '#555' }}>{item.label}</span>
                  <span style={{ fontWeight: 'bold' }}>{item.value.toFixed ? item.value.toFixed(1) : item.value} {item.unit}</span>
                </div>
              ))}
            </div>
            <div style={{ textAlign: 'center' }}>
              <button 
                className="btn btn-secondary"
                onClick={closeDetails}
              >
                关闭
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* 操作按钮 */}
      <motion.div 
        style={{ marginTop: '40px', textAlign: 'center' }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <button 
          className="btn btn-primary" 
          onClick={() => navigate('/measurement')}
          style={{ marginRight: '16px' }}
        >
          开始新测量
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

export default HistoryPage