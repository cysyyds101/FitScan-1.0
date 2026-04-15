import React from 'react'
import { Link } from 'react-router-dom'

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="container navbar-container">
        <Link to="/" className="navbar-logo">
          FitScan
        </Link>
        <ul className="navbar-links">
          <li><Link to="/">首页</Link></li>
          <li><Link to="/measurement">开始测量</Link></li>
          <li><Link to="/history">历史记录</Link></li>
        </ul>
      </div>
    </nav>
  )
}

export default Navbar