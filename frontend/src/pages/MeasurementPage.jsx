import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../utils/api'

const MeasurementPage = () => {
  const [step, setStep] = useState(1) // 1: 准备阶段, 2: 校准阶段, 3: 测量阶段
  const [isCameraActive, setIsCameraActive] = useState(false)
  const [referenceDetected, setReferenceDetected] = useState(false)
  const [measurementData, setMeasurementData] = useState(null)
  const [loading, setLoading] = useState(false)
  const videoRef = useRef(null)
  const navigate = useNavigate()

  // 模拟检测到的参照物类型
  const [referenceType, setReferenceType] = useState(null)

  // 开始摄像头
  const startCamera = async () => {
    try {
      setLoading(true)
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setIsCameraActive(true)
      }
      setLoading(false)
    } catch (error) {
      console.error('Error accessing camera:', error)
      setLoading(false)
    }
  }

  // 停止摄像头
  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject
      stream.getTracks().forEach(track => track.stop())
      setIsCameraActive(false)
    }
  }

  // 模拟参照物检测
  const detectReference = async () => {
    setLoading(true)
    try {
      const response = await api.detectReference('A4')
      if (response.data.detected) {
        setReferenceDetected(true)
        setReferenceType(response.data.referenceType)
        setStep(3) // 进入测量阶段
      }
    } catch (error) {
      console.error('Error detecting reference:', error)
    } finally {
      setLoading(false)
    }
  }

  // 模拟开始测量
  const startMeasurement = async () => {
    setLoading(true)
    try {
      const response = await api.startMeasurement()
      const measurementData = response.data
      setMeasurementData(measurementData)
      // 跳转到结果页面
      navigate('/result', { state: { measurementData } })
    } catch (error) {
      console.error('Error starting measurement:', error)
    } finally {
      setLoading(false)
    }
  }

  // 重新校准
  const recalibrate = () => {
    setStep(2)
    setReferenceDetected(false)
    setReferenceType(null)
  }

  // 组件卸载时停止摄像头
  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  return (
    <div className="measurement-page" style={{ margin: '40px 0' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '40px' }}>智能尺寸测量</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px', alignItems: 'center' }} className="grid grid-cols-2">
        {/* 左侧：摄像头显示 */}
        <motion.div 
          className="card"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div style={{ position: 'relative', aspectRatio: '16/9', backgroundColor: '#000', borderRadius: '8px', overflow: 'hidden' }}>
            {isCameraActive ? (
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline 
                style={{ width: '100%', height: '100%' }}
              />
            ) : (
              <div style={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                height: '100%', 
                color: '#fff' 
              }}>
                摄像头未激活
              </div>
            )}
            
            {/* 加载动画 */}
            {loading && (
              <div style={{ 
                position: 'absolute', 
                top: 0, 
                left: 0, 
                right: 0, 
                bottom: 0, 
                backgroundColor: 'rgba(0, 0, 0, 0.7)', 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center' 
              }}>
                <div className="loading-spinner"></div>
              </div>
            )}
            
            {/* 步骤提示 */}
            {step === 2 && !referenceDetected && (
              <div style={{ 
                position: 'absolute', 
                bottom: 0, 
                left: 0, 
                right: 0, 
                backgroundColor: 'rgba(0, 0, 0, 0.7)', 
                color: '#fff', 
                padding: '16px', 
                textAlign: 'center' 
              }}>
                请将A4纸、身份证或银行卡贴近胸前，确保清晰可见
              </div>
            )}
            
            {step === 3 && (
              <div style={{ 
                position: 'absolute', 
                bottom: 0, 
                left: 0, 
                right: 0, 
                backgroundColor: 'rgba(0, 0, 0, 0.7)', 
                color: '#fff', 
                padding: '16px', 
                textAlign: 'center' 
              }}>
                请保持自然站姿，微微张开双臂
              </div>
            )}
          </div>
        </motion.div>

        {/* 右侧：控制面板 */}
        <motion.div 
          className="card"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 style={{ marginBottom: '30px' }}>测量控制</h2>
          
          {step === 1 && (
            <div>
              <h3>准备阶段</h3>
              <p style={{ marginBottom: '20px', color: '#666' }}>请确保您有以下物品：</p>
              <ul style={{ listStyle: 'disc', paddingLeft: '20px', marginBottom: '30px', color: '#666' }}>
                <li>一台带有摄像头的设备</li>
                <li>A4纸、身份证或银行卡作为参照物</li>
                <li>充足的光线条件</li>
                <li>简洁的背景环境</li>
              </ul>
              <button 
                className="btn btn-primary" 
                onClick={startCamera}
                style={{ width: '100%', marginBottom: '16px' }}
              >
                启动摄像头
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={() => navigate('/')}
                style={{ width: '100%' }}
              >
                返回首页
              </button>
            </div>
          )}
          
          {step === 2 && (
            <div>
              <h3>校准阶段</h3>
              <p style={{ marginBottom: '20px', color: '#666' }}>请将参照物贴近胸前，确保清晰可见</p>
              {referenceType && (
                <div className="success-message" style={{ marginBottom: '20px' }}>
                  已检测到 {referenceType} 参照物
                </div>
              )}
              <button 
                className="btn btn-primary" 
                onClick={detectReference}
                disabled={loading}
                style={{ width: '100%', marginBottom: '16px' }}
              >
                {loading ? '检测中...' : '开始检测参照物'}
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={stopCamera}
                style={{ width: '100%' }}
              >
                关闭摄像头
              </button>
            </div>
          )}
          
          {step === 3 && (
            <div>
              <h3>测量阶段</h3>
              <p style={{ marginBottom: '20px', color: '#666' }}>请保持自然站姿，微微张开双臂</p>
              <div className="success-message" style={{ marginBottom: '20px' }}>
                校准成功！参照物：{referenceType}
              </div>
              <button 
                className="btn btn-primary" 
                onClick={startMeasurement}
                disabled={loading}
                style={{ width: '100%', marginBottom: '16px' }}
              >
                {loading ? '测量中...' : '开始测量'}
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={recalibrate}
                style={{ width: '100%', marginBottom: '16px' }}
              >
                重新校准
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={stopCamera}
                style={{ width: '100%' }}
              >
                关闭摄像头
              </button>
            </div>
          )}
        </motion.div>
      </div>

      {/* 测量步骤指示器 */}
      <div style={{ marginTop: '40px', textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginBottom: '10px' }}>
          {[1, 2, 3].map((stepNum) => (
            <div 
              key={stepNum}
              style={{
                width: '100px',
                height: '4px',
                backgroundColor: stepNum <= step ? '#4CAF50' : '#ddd',
                borderRadius: '2px',
                transition: 'background-color 0.3s ease'
              }}
            ></div>
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '40px' }}>
          <span style={{ color: step === 1 ? '#4CAF50' : '#666', fontWeight: step === 1 ? 'bold' : 'normal' }}>准备</span>
          <span style={{ color: step === 2 ? '#4CAF50' : '#666', fontWeight: step === 2 ? 'bold' : 'normal' }}>校准</span>
          <span style={{ color: step === 3 ? '#4CAF50' : '#666', fontWeight: step === 3 ? 'bold' : 'normal' }}>测量</span>
        </div>
      </div>
    </div>
  )
}

export default MeasurementPage