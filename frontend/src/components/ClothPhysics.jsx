/**
 * ClothPhysics.jsx — 伪布料（vertex offset）独立组件。
 *
 * 规则（Virtual Try-On Rule）：
 *  - 禁止 full physics cloth engine
 *  - 禁止 GPU compute shader cloth simulation
 *  - 允许"伪布料"：vertex offset / 简化动画
 *
 * 实现：
 *  - 用 R3F 的 useFrame 钩子，每帧对子节点的 group.position.y 加一个 sin 波偏移
 *  - baseY = 用户/transform 指定的静态 Y，作为基准线
 *  - amplitude / frequency 暴露为可调 prop（后续 ClothPhysicsController 可用）
 *  - enabled=false 时直接渲染 children，不做任何动画（保持 group 位置由 transform 控制）
 *
 * 作用域：
 *  - 该组件只负责"在 transform 之外叠加时间相关的微动"
 *  - 不负责 mesh 创建、不负责 transform 写入（由 ClothingOverlay 负责）
 */
import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';

/**
 * @param {Object} props
 * @param {boolean} [props.enabled=true]     是否启用伪布料动画
 * @param {number}  [props.baseY=0]          基准 Y 位置（通常来自 transform.position[1]）
 * @param {number}  [props.amplitude=0.012]  顶点 Y 偏移振幅（米）
 * @param {number}  [props.frequency=2.0]    sin 波频率（弧度/秒）
 * @param {number}  [props.phase=0]          相位偏移，用于多件服装错开节奏
 * @param {React.ReactNode} props.children   被包裹的 3D 节点
 */
export default function ClothPhysics({
  enabled = true,
  baseY = 0,
  amplitude = 0.012,
  frequency = 2.0,
  phase = 0,
  children,
}) {
  const groupRef = useRef();

  useFrame(({ clock }) => {
    if (!enabled || !groupRef.current) return;
    const t = clock.elapsedTime;
    groupRef.current.position.y = baseY + Math.sin(t * frequency + phase) * amplitude;
  });

  // 注意：groupRef.current.position.y 在 enabled=false 时不会被 useFrame 触碰，
  // 保持 children 自己声明的 position。
  return <group ref={groupRef}>{children}</group>;
}
