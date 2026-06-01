/**
 * FitScan ECharts 图表组件
 * 提供雷达图、折线图、仪表盘等多种图表
 */
import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { Card } from './ui'

// 雷达图 - 体型数据展示
export function RadarChart({ data, onClick }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: '#00ffff',
        textStyle: { color: '#fff' }
      },
      radar: {
        indicator: data?.indicators || [
          { name: '身高', max: 200 },
          { name: '肩宽', max: 60 },
          { name: '胸围', max: 130 },
          { name: '腰围', max: 120 },
          { name: '臀围', max: 130 },
          { name: '臂长', max: 100 }
        ],
        shape: 'polygon',
        splitNumber: 5,
        axisName: {
          color: '#fff',
          fontSize: 12
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(0, 255, 255, 0.2)'
          }
        },
        splitArea: {
          show: true,
          areaStyle: {
            color: ['rgba(0, 255, 255, 0.05)', 'rgba(0, 255, 255, 0.1)']
          }
        },
        axisLine: {
          lineStyle: {
            color: 'rgba(0, 255, 255, 0.3)'
          }
        }
      },
      series: [{
        type: 'radar',
        data: [{
          value: data?.values || [170, 45, 95, 80, 95, 70],
          name: '体型数据',
          lineStyle: {
            color: '#00ffff',
            width: 2
          },
          areaStyle: {
            color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
              { offset: 0, color: 'rgba(0, 255, 255, 0.4)' },
              { offset: 1, color: 'rgba(0, 255, 255, 0.1)' }
            ])
          },
          itemStyle: {
            color: '#00ffff'
          },
          symbol: 'circle',
          symbolSize: 6
        }]
      }]
    }

    chartInstance.current.setOption(option)

    if (onClick) {
      chartInstance.current.on('click', onClick)
    }

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.current?.dispose()
    }
  }, [data])

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height: '100%', minHeight: '300px' }}
    />
  )
}

// 折线图 - 历史趋势
export function LineChart({ data, xAxisData, seriesData, title, color = '#00ffff' }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: color,
        textStyle: { color: '#fff' },
        formatter: (params) => {
          const item = params[0]
          return `${item.name}<br/>${item.seriesName}: ${item.value}${item.seriesName.includes('围') || item.seriesName.includes('高') ? 'cm' : 'kg'}`
        }
      },
      grid: {
        left: '10%',
        right: '5%',
        top: '15%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: xAxisData || ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.3)' } },
        axisLabel: { color: 'rgba(255,255,255,0.7)' }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        axisLabel: { color: 'rgba(255,255,255,0.7)' }
      },
      series: [{
        name: title || '数据',
        type: 'line',
        smooth: true,
        data: seriesData || [82, 93, 90, 93, 129, 133, 132],
        lineStyle: { color, width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: `${color}66` },
            { offset: 1, color: `${color}00` }
          ])
        },
        itemStyle: { color },
        symbol: 'circle',
        symbolSize: 8
      }]
    }

    chartInstance.current.setOption(option)

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.current?.dispose()
    }
  }, [data, xAxisData, seriesData, title, color])

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height: '100%', minHeight: '250px' }}
    />
  )
}

// 仪表盘 - 单一指标展示
export function GaugeChart({ value, max = 100, label = '完成度', color = '#00ffff' }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)

    const option = {
      backgroundColor: 'transparent',
      series: [{
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: max,
        radius: '90%',
        splitNumber: 10,
        axisLine: {
          lineStyle: {
            width: 15,
            color: [
              [0.3, '#ff4444'],
              [0.7, `${color}99`],
              [1, color]
            ]
          }
        },
        pointer: {
          icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
          length: '60%',
          width: 8,
          offsetCenter: [0, '-40%'],
          itemStyle: { color }
        },
        axisTick: {
          length: 8,
          lineStyle: { color: 'auto', width: 1 }
        },
        splitLine: {
          length: 15,
          lineStyle: { color: 'auto', width: 2 }
        },
        axisLabel: {
          color: 'rgba(255,255,255,0.5)',
          fontSize: 10,
          distance: -60
        },
        title: {
          show: false
        },
        detail: {
          fontSize: 24,
          fontWeight: 'bold',
          color: '#fff',
          offsetCenter: [0, '30%'],
          valueAnimation: true,
          formatter: (val) => Math.round(val)
        },
        data: [{ value: value || 0, name: label }]
      }]
    }

    chartInstance.current.setOption(option)

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.current?.dispose()
    }
  }, [value, max, label, color])

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height: '100%', minHeight: '200px' }}
    />
  )
}

// 饼图 - 尺码分布
export function PieChart({ data, title = '尺码分布' }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  const defaultColors = ['#00ffff', '#ff00ff', '#ffff00', '#00ff00', '#ff6600', '#ff0066']

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)

    const pieData = data || [
      { value: 30, name: 'S' },
      { value: 50, name: 'M' },
      { value: 40, name: 'L' },
      { value: 20, name: 'XL' },
      { value: 10, name: 'XXL' }
    ]

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: '#00ffff',
        textStyle: { color: '#fff' }
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: { color: '#fff' }
      },
      series: [{
        name: title,
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#1a1a2e',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
            color: '#fff'
          }
        },
        labelLine: { show: false },
        data: pieData.map((item, index) => ({
          ...item,
          itemStyle: { color: defaultColors[index % defaultColors.length] }
        }))
      }]
    }

    chartInstance.current.setOption(option)

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.current?.dispose()
    }
  }, [data, title])

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height: '100%', minHeight: '250px' }}
    />
  )
}

// 多指标对比图
export function MultiLineChart({ data, title = '指标趋势对比' }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  const colors = ['#00ffff', '#ff00ff', '#ffff00', '#00ff00']

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)

    const xAxisData = data?.dates || ['1月', '2月', '3月', '4月', '5月', '6月']
    const series = data?.series || [
      { name: '身高', data: [170, 171, 172, 171, 173, 174] },
      { name: '胸围', data: [92, 93, 94, 93, 95, 96] },
      { name: '腰围', data: [78, 79, 78, 77, 76, 76] },
      { name: '臀围', data: [94, 95, 95, 94, 94, 95] }
    ]

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: '#00ffff',
        textStyle: { color: '#fff' }
      },
      legend: {
        data: series.map(s => s.name),
        textStyle: { color: '#fff' },
        top: '5%'
      },
      grid: {
        left: '10%',
        right: '5%',
        top: '20%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.3)' } },
        axisLabel: { color: 'rgba(255,255,255,0.7)' }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        axisLabel: { color: 'rgba(255,255,255,0.7)' }
      },
      series: series.map((s, index) => ({
        name: s.name,
        type: 'line',
        smooth: true,
        data: s.data,
        lineStyle: { color: colors[index], width: 2 },
        itemStyle: { color: colors[index] },
        symbol: 'circle',
        symbolSize: 6
      }))
    }

    chartInstance.current.setOption(option)

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.current?.dispose()
    }
  }, [data, title])

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height: '100%', minHeight: '300px' }}
    />
  )
}

// 热力图 - 时间分布
export function HeatmapChart({ data }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)

    const hours = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
                   '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

    // 随机生成热力数据
    const heatmapData = []
    for (let i = 0; i < days.length; i++) {
      for (let j = 0; j < hours.length; j++) {
        heatmapData.push([j, i, Math.floor(Math.random() * 100)])
      }
    }

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        position: 'top',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: '#00ffff',
        textStyle: { color: '#fff' },
        formatter: (params) => `${days[params.value[1]]} ${hours[params.value[0]]}:00<br/>测量次数: ${params.value[2]}`
      },
      grid: {
        left: '15%',
        right: '10%',
        top: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: hours,
        splitArea: { show: true },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.3)' } },
        axisLabel: { color: 'rgba(255,255,255,0.7)', interval: 3 }
      },
      yAxis: {
        type: 'category',
        data: days,
        splitArea: { show: true },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.3)' } },
        axisLabel: { color: 'rgba(255,255,255,0.7)' }
      },
      visualMap: {
        min: 0,
        max: 100,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        textStyle: { color: '#fff' },
        inRange: {
          color: ['#1a1a2e', '#16213e', '#0f3460', '#00ffff', '#ff00ff']
        }
      },
      series: [{
        name: '测量次数',
        type: 'heatmap',
        data: heatmapData,
        label: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }

    chartInstance.current.setOption(option)

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.current?.dispose()
    }
  }, [data])

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height: '100%', minHeight: '300px' }}
    />
  )
}

export default {
  RadarChart,
  LineChart,
  GaugeChart,
  PieChart,
  MultiLineChart,
  HeatmapChart
}
