import { useState, useEffect } from 'react'

function App() {
  const [healthStatus, setHealthStatus] = useState<string>('Checking...')

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => res.json())
      .then((data) => setHealthStatus(`Backend OK - v${data.version}`))
      .catch((err) => setHealthStatus('Backend Unreachable'))
  }, [])

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 text-slate-100 font-sans">
      <div className="p-8 border border-slate-700 bg-slate-800 rounded-xl shadow-2xl max-w-md w-full text-center">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent mb-4">
          IPL Auction Simulator
        </h1>
        <p className="text-slate-400 mb-8">AI-Powered Multi-franchise Auction</p>
        
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-900 border border-slate-700 text-sm">
          <span className={`w-2 h-2 rounded-full ${healthStatus.includes('OK') ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
          {healthStatus}
        </div>
      </div>
    </div>
  )
}

export default App
