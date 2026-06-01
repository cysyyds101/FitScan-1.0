/**
 * FitScan ECharts 纹理组件
 * 将 ECharts 渲染的 Canvas 作为纹理贴到 Three.js 物体上
 */
import React, { useRef, useEffect, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import * as echarts from 'echarts'

// 将 ECharts Canvas 转换为 Three.js 纹理
export function useEChartsTexture(option, size = [512, 256], updateInterval = 1000) {
  const canvasRef = useRef(null)
  const textureRef = useRef(null)
  const chartRef = useRef(null)

  // 创建 Canvas
  useEffect(() => {
    const canvas = document.createElement('canvas')
    canvas.width = size[0]
    canvas.height = size[1]
    canvasRef.current = canvas

    // 初始化 ECharts
    const chart = echarts.init(canvas, null, {
      width: size[0],
      height: size[1]
    })
    chart.setOption(option)
    chartRef.current = chart

    // 创建纹理
    const texture = new THREE.CanvasTexture(canvas)
    texture.minFilter = THREE.LinearFilter
    texture.magFilter = THREE.LinearFilter
    texture.needsUpdate = true
    textureRef.current = texture

    // 定时更新纹理
    const interval = setInterval(() => {
      if (chartRef.current) {
        chartRef.current.setOption(option)
        if (textureRef.current) {
          textureRef.current.needsUpdate = true
        }
      }
    }, updateInterval)

    return () => {
      clearInterval(interval)
      chart.dispose()
      texture.dispose()
    }
  }, [])

  return { canvasRef, textureRef, chartRef }
}

// 3D 平面上的 ECharts 图表
export function ChartOn3DPlane({ option, position = [0, 0, 0], size = [2, 1], updateInterval = 1000 }) {
  const meshRef = useRef()
  const { textureRef } = useEChartsTexture(option, [512, 256], updateInterval)

  useFrame(() => {
    if (meshRef.current && textureRef.current) {
      textureRef.current.needsUpdate = true
    }
  })

  return (
    <mesh ref={meshRef} position={position}>
      <planeGeometry args={size} />
      <meshBasicMaterial
        map={textureRef.current}
        transparent={true}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}

// 带有边框的图表面板
export function ChartPanel3D({
  option,
  position = [0, 0, 0],
  size = [2, 1],
  updateInterval = 1000,
  frameColor = '#00ffff'
}) {
  const groupRef = useRef()
  const { textureRef } = useEChartsTexture(option, [512, 256], updateInterval)

  return (
    <group ref={groupRef} position={position}>
      {/* 图表面板 */}
      <mesh position={[0, 0, 0.01]}>
        <planeGeometry args={size} />
        <meshBasicMaterial
          map={textureRef.current}
          transparent={true}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* 边框 - 顶部 */}
      <mesh position={[0, size[1] / 2 + 0.01, 0]}>
        <boxGeometry args={[size[0] + 0.02, 0.02, 0.02]} />
        <meshBasicMaterial color={frameColor} />
      </mesh>

      {/* 边框 - 底部 */}
      <mesh position={[0, -size[1] / 2 - 0.01, 0]}>
        <boxGeometry args={[size[0] + 0.02, 0.02, 0.02]} />
        <meshBasicMaterial color={frameColor} />
      </mesh>

      {/* 边框 - 左侧 */}
      <mesh position={[-size[0] / 2 - 0.01, 0, 0]}>
        <boxGeometry args={[0.02, size[1], 0.02]} />
        <meshBasicMaterial color={frameColor} />
      </mesh>

      {/* 边框 - 右侧 */}
      <mesh position={[size[0] / 2 + 0.01, 0, 0]}>
        <boxGeometry args={[0.02, size[1], 0.02]} />
        <meshBasicMaterial color={frameColor} />
      </mesh>
    </group>
  )
}

// 仪表盘样式的 3D 图表
export function GaugeOn3D({
  value,
  max = 100,
  position = [0, 0, 0],
  radius = 1,
  color = '#00ffff'
}) {
  const meshRef = useRef()
  const textureRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 256
    canvas.height = 256
    textureRef.current = new THREE.CanvasTexture(canvas)
    textureRef.current.minFilter = THREE.LinearFilter

    chartRef.current = echarts.init(canvas)
    updateChart()

    return () => {
      chartRef.current?.dispose()
      textureRef.current?.dispose()
    }
  }, [])

  const updateChart = () => {
    if (!chartRef.current) return
    chartRef.current.setOption({
      series: [{
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: max,
        radius: '100%',
        center: ['50%', '70%'],
        pointer: { show: false },
        axisLine: {
          lineStyle: {
            width: 20,
            color: [[value / max, color], [1, 'rgba(255,255,255,0.1)']]
          }
        },
        detail: {
          fontSize: 32,
          fontWeight: 'bold',
          color: '#fff',
          offsetCenter: [0, -10],
          formatter: (val) => Math.round(val)
        },
        data: [{ value, name: '完成度' }],
        title: { show: false }
      }]
    })
    if (textureRef.current) {
      textureRef.current.needsUpdate = true
    }
  }

  useEffect(() => {
    updateChart()
  }, [value, max, color])

  useFrame(() => {
    if (meshRef.current && textureRef.current) {
      meshRef.current.rotation.z += 0.002
      textureRef.current.needsUpdate = true
    }
  })

  return (
    <mesh ref={meshRef} position={position}>
      <circleGeometry args={[radius, 64]} />
      <meshBasicMaterial map={textureRef.current} transparent />
    </mesh>
  )
}

export default {
  useEChartsTexture,
  ChartOn3DPlane,
  ChartPanel3D,
  GaugeOn3D
}
