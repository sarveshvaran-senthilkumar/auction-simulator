export default function RetentionPhase() {
  return (
    <div className="flex min-h-screen bg-slate-900 text-white">
      <div className="w-1/3 p-6 border-r border-slate-700 overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Your 2024 Squad</h2>
        {/* Map through squad entries here */}
        <div className="p-4 bg-slate-800 rounded-lg mb-2">Player Card Stub</div>
      </div>
      
      <div className="w-1/3 p-6 flex flex-col items-center">
        <h2 className="text-xl font-bold mb-8">Retention Slots</h2>
        {/* Render retention slabs */}
        {[1, 2, 3, 4, 5].map((slot) => (
          <div key={slot} className="w-full max-w-sm h-16 border-2 border-dashed border-slate-600 rounded-lg mb-4 flex items-center justify-center text-slate-500">
            Slot {slot} (Capped)
          </div>
        ))}
        <div className="w-full max-w-sm h-16 border-2 border-dashed border-slate-600 rounded-lg mb-4 flex items-center justify-center text-slate-500">
          Uncapped Slot
        </div>
      </div>
      
      <div className="w-1/3 p-6 border-l border-slate-700">
        <h2 className="text-xl font-bold mb-4">Purse Status</h2>
        <div className="w-full bg-slate-800 h-8 rounded-full overflow-hidden mb-8">
          <div className="bg-green-500 h-full w-full"></div>
        </div>
        
        <h3 className="text-lg mb-2">RTM Cards Preview: 6</h3>
        
        <button className="w-full py-4 mt-auto bg-blue-600 hover:bg-blue-500 rounded-lg font-bold">
          Confirm Retentions
        </button>
      </div>
    </div>
  )
}
