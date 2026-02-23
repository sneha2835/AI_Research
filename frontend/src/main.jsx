import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

/* ================= THEME INIT ================= */

// Default is light (do nothing)
// Only apply dark if saved in localStorage
const savedTheme = localStorage.getItem('theme')

if (savedTheme === 'dark') {
  document.body.classList.add('dark-mode')
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)