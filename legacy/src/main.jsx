import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

try {
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
  if (window.__diag && window.__diag.ok) window.__diag.ok()
} catch (err) {
  if (window.__diag) window.__diag.log('ERROR render: ' + (err && err.message ? err.message : err))
  else document.getElementById('root').innerHTML = '<pre style="padding:20px;color:#b91c1c">' + (err && err.stack ? err.stack : err) + '</pre>'
}
