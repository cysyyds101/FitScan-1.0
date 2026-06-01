import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="container navbar-container">
        <Link to="/" className="navbar-logo">
          <motion.span
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.2 }}
          >
            FitScan
          </motion.span>
        </Link>
        <ul className="navbar-links">
          <li>
            <Link to="/">首页</Link>
          </li>
          <li>
            <Link to="/measurement">开始测量</Link>
          </li>
          <li>
            <Link to="/history">历史记录</Link>
          </li>
          <li>
            <Link to="/dashboard">数据看板</Link>
          </li>
          <li>
            <Link to="/virtual-tryon">虚拟换衣</Link>
          </li>
        </ul>
      </div>
    </nav>
  )
}

export default Navbar