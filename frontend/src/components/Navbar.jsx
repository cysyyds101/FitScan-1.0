/**
 * Navbar.jsx — 全站导航栏。
 *
 * 取代每个页面里的 <header className="topbar">，统一 logo + 导航。
 * 路径通过 window.location.pathname 读取，避免引入额外的 router hook。
 */
export default function Navbar() {
  const path = window.location.pathname;
  const isActive = (p) => path === p;
  return (
    <header className="topbar">
      <div className="logo">
        FitScan <span className="tag">Beta</span>
      </div>
      <nav className="topbar-nav">
        <a
          href="/virtual-tryon"
          className={isActive('/virtual-tryon') ? 'nav-link active' : 'nav-link'}
        >
          虚拟试衣
        </a>
        <a
          href="/measure"
          className={isActive('/measure') ? 'nav-link active' : 'nav-link'}
        >
          测量
        </a>
      </nav>
    </header>
  );
}
