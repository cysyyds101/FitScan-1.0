import { Component } from 'react';

/**
 * ErrorBoundary.jsx — 全局错误边界。
 *
 * 捕获子树渲染时抛出的错误，避免整页白屏。
 * 生产环境可扩展为上报到 Sentry / Datadog。
 */
export default class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(e) {
    return { error: e };
  }

  componentDidCatch(e, info) {
    console.error('[ErrorBoundary]', e, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            background: '#0b1220',
            color: '#fca5a5',
            gap: 12,
          }}
        >
          <div style={{ fontSize: 32 }}>⚠️</div>
          <div style={{ fontSize: 14 }}>{this.state.error.message}</div>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: 8,
              padding: '8px 20px',
              background: '#3b82f6',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
            }}
          >
            重新加载
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
