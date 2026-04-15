import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

const HomePage = () => {
  return (
    <div className="home-page">
      {/* 英雄区域 */}
      <motion.section 
        className="hero-section" 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        style={{
          padding: '100px 0',
          textAlign: 'center',
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
          borderRadius: '12px',
          margin: '40px 0'
        }}
      >
        <h1 style={{ fontSize: '3rem', marginBottom: '20px', color: '#2c3e50' }}>FitScan</h1>
        <p style={{ fontSize: '1.2rem', marginBottom: '40px', color: '#555', maxWidth: '800px', marginLeft: 'auto', marginRight: 'auto' }}>
          智能人体尺寸估算系统，利用普通摄像头和已知尺寸的参照物，快速测量人体尺寸并推荐服装尺码
        </p>
        <Link to="/measurement" className="btn btn-primary" style={{ fontSize: '1.1rem', padding: '15px 30px' }}>
          开始测量
        </Link>
      </motion.section>

      {/* 核心功能 */}
      <section className="features-section" style={{ margin: '80px 0' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '60px' }}>核心功能</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '30px' }}>
          {[
            {
              title: '实时视频采集',
              description: '使用摄像头实时采集视频，支持多种分辨率设置',
              icon: '📹'
            },
            {
              title: '参照物检测',
              description: '自动识别A4纸、身份证或银行卡，计算像素与真实长度的比例',
              icon: '📄'
            },
            {
              title: '人体关键点提取',
              description: '使用MediaPipe Pose提取33个人体关键点',
              icon: '👤'
            },
            {
              title: '尺寸计算',
              description: '精确计算肩宽、臂长、腿长、身高、胸围、腰围、臀围',
              icon: '📏'
            },
            {
              title: '体型分析',
              description: '雷达图可视化展示人体体型轮廓',
              icon: '📊'
            },
            {
              title: '尺码推荐',
              description: '根据测量结果推荐服装尺码（宽松版/修身版）',
              icon: '👕'
            }
          ].map((feature, index) => (
            <motion.div 
              key={index} 
              className="card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div style={{ fontSize: '2.5rem', marginBottom: '20px' }}>{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p style={{ color: '#666' }}>{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* 使用流程 */}
      <section className="process-section" style={{ margin: '80px 0' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '60px' }}>使用流程</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '40px' }}>
          {[
            {
              step: 'Step 1',
              title: '准备参照物',
              description: '准备A4纸、身份证或银行卡作为参照物'
            },
            {
              step: 'Step 2',
              title: '校准系统',
              description: '将参照物贴近胸前，系统自动检测并完成校准'
            },
            {
              step: 'Step 3',
              title: '开始测量',
              description: '站在摄像头前，保持自然站姿，微微张开双臂'
            },
            {
              step: 'Step 4',
              title: '查看结果',
              description: '系统实时显示测量数据和推荐尺码'
            }
          ].map((step, index) => (
            <motion.div 
              key={index} 
              style={{ 
                textAlign: 'center', 
                maxWidth: '250px',
                position: 'relative'
              }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div style={{ 
                width: '80px', 
                height: '80px', 
                borderRadius: '50%', 
                background: '#4CAF50', 
                color: 'white', 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                fontSize: '1.2rem', 
                fontWeight: 'bold',
                margin: '0 auto 20px'
              }}>
                {index + 1}
              </div>
              <h3>{step.title}</h3>
              <p style={{ color: '#666' }}>{step.description}</p>
              {index < 3 && (
                <div style={{ 
                  position: 'absolute', 
                  top: '40px', 
                  right: '-20px', 
                  width: '40px', 
                  height: '2px', 
                  background: '#ddd',
                  display: {xs: 'none', md: 'block'}
                }}>
                  <div style={{ 
                    position: 'absolute', 
                    right: '-5px', 
                    top: '-4px', 
                    width: '10px', 
                    height: '10px', 
                    borderRadius: '50%', 
                    background: '#4CAF50'
                  }}></div>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* 技术特点 */}
      <section className="tech-section" style={{ margin: '80px 0' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '60px' }}>技术特点</h2>
        <div className="card">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '30px' }}>
            {[
              { label: '测量精度', value: '±2-5cm' },
              { label: '处理性能', value: '30 FPS' },
              { label: '响应时间', value: '<100ms' },
              { label: '内存占用', value: '<500MB' },
              { label: '支持系统', value: 'Windows/macOS/Linux' },
              { label: '摄像头要求', value: '普通网络摄像头' }
            ].map((item, index) => (
              <div key={index} style={{ textAlign: 'center' }}>
                <h4 style={{ marginBottom: '10px', color: '#555' }}>{item.label}</h4>
                <p style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#4CAF50' }}>{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 开始测量按钮 */}
      <section style={{ textAlign: 'center', margin: '80px 0' }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Link to="/measurement" className="btn btn-primary" style={{ fontSize: '1.2rem', padding: '18px 36px' }}>
            立即开始测量
          </Link>
        </motion.div>
      </section>
    </div>
  )
}

export default HomePage