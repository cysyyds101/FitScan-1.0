/**
 * FitScan UI 组件
 * 基础 UI 组件库
 */
import React from 'react'

// 卡片组件
export function Card({ children, className = '', title, ...props }) {
  return (
    <div className={`card ${className}`} {...props}>
      {title && <div className="card-header">{title}</div>}
      <div className="card-body">{children}</div>
    </div>
  )
}

// 按钮组件
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  ...props
}) {
  const variants = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    outline: 'btn-outline',
    ghost: 'btn-ghost'
  }

  const sizes = {
    sm: 'btn-sm',
    md: 'btn-md',
    lg: 'btn-lg'
  }

  return (
    <button
      className={`btn ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}

// 加载状态组件
export function Spinner({ size = 'md', color = '#00ffff' }) {
  const sizes = {
    sm: 20,
    md: 40,
    lg: 60
  }

  return (
    <div
      className="spinner"
      style={{
        width: sizes[size],
        height: sizes[size],
        borderWidth: sizes[size] / 8,
        borderColor: `${color}33`,
        borderTopColor: color
      }}
    />
  )
}

// 加载指示器
export function Loading({ text = '加载中...', overlay = false }) {
  if (overlay) {
    return (
      <div className="loading-overlay">
        <Spinner size="lg" />
        <p>{text}</p>
      </div>
    )
  }

  return (
    <div className="loading-inline">
      <Spinner />
      <span>{text}</span>
    </div>
  )
}

// 空状态组件
export function EmptyState({ icon = '📭', title, description, action }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <h3 className="empty-title">{title}</h3>
      {description && <p className="empty-description">{description}</p>}
      {action && <div className="empty-action">{action}</div>}
    </div>
  )
}

// 徽章组件
export function Badge({ children, variant = 'default', className = '' }) {
  const variants = {
    default: 'badge-default',
    primary: 'badge-primary',
    success: 'badge-success',
    warning: 'badge-warning',
    danger: 'badge-danger'
  }

  return (
    <span className={`badge ${variants[variant]} ${className}`}>
      {children}
    </span>
  )
}

// 头像组件
export function Avatar({ src, alt = 'Avatar', size = 'md', fallback }) {
  const sizes = {
    sm: 32,
    md: 40,
    lg: 56,
    xl: 80
  }

  const [error, setError] = React.useState(false)

  if (!src || error) {
    return (
      <div
        className="avatar avatar-fallback"
        style={{ width: sizes[size], height: sizes[size] }}
      >
        {fallback || alt[0]?.toUpperCase()}
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      className="avatar"
      style={{ width: sizes[size], height: sizes[size] }}
      onError={() => setError(true)}
    />
  )
}

// 进度条组件
export function Progress({ value, max = 100, color = '#00ffff', showLabel = true }) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  return (
    <div className="progress-container">
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{
            width: `${percentage}%`,
            backgroundColor: color
          }}
        />
      </div>
      {showLabel && (
        <span className="progress-label">{Math.round(percentage)}%</span>
      )}
    </div>
  )
}

// 标签页组件
export function Tabs({ tabs, activeTab, onChange, className = '' }) {
  return (
    <div className={`tabs ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.icon && <span className="tab-icon">{tab.icon}</span>}
          <span className="tab-label">{tab.label}</span>
        </button>
      ))}
    </div>
  )
}

// 模态框组件
export function Modal({ isOpen, onClose, title, children, footer }) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}

// 工具提示组件
export function Tooltip({ children, content, position = 'top' }) {
  const [visible, setVisible] = React.useState(false)

  return (
    <div
      className="tooltip-wrapper"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div className={`tooltip tooltip-${position}`}>{content}</div>
      )}
    </div>
  )
}

// 下拉菜单组件
export function Dropdown({ trigger, children, align = 'left' }) {
  const [open, setOpen] = React.useState(false)
  const dropdownRef = React.useRef(null)

  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="dropdown" ref={dropdownRef}>
      <div onClick={() => setOpen(!open)}>{trigger}</div>
      {open && (
        <div className={`dropdown-menu dropdown-${align}`} onClick={() => setOpen(false)}>
          {children}
        </div>
      )}
    </div>
  )
}

export function DropdownItem({ children, onClick, icon, danger = false }) {
  return (
    <div
      className={`dropdown-item ${danger ? 'danger' : ''}`}
      onClick={onClick}
    >
      {icon && <span className="dropdown-item-icon">{icon}</span>}
      <span>{children}</span>
    </div>
  )
}

export default {
  Card,
  Button,
  Spinner,
  Loading,
  EmptyState,
  Badge,
  Avatar,
  Progress,
  Tabs,
  Modal,
  Tooltip,
  Dropdown,
  DropdownItem
}
