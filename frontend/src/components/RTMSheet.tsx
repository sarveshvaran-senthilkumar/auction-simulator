import { useEffect, useState } from 'react'
import { haptic, money } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import { Avatar, BottomSheet, Button, RoleChip } from './ui'

/** The two decisions a human has to make outside of bidding:
 *  exercising an RTM card, and the one counter-raise the losing bidder gets.
 *
 *  Not dismissible — the backend is blocking on an answer, and silence means no.
 */
export function RTMSheet({ decide }: { decide: (choice: boolean) => void }) {
  const decision = useAuction((s) => s.decision)
  const clearDecision = useAuction((s) => s.clearDecision)
  const [left, setLeft] = useState(0)

  useEffect(() => {
    if (!decision) return
    setLeft(decision.seconds)
    const id = window.setInterval(() => {
      setLeft((prev) => {
        if (prev <= 1) {
          window.clearInterval(id)
          clearDecision()
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => window.clearInterval(id)
  }, [decision, clearDecision])

  function answer(choice: boolean) {
    haptic(choice ? [20, 40, 20] : 12)
    decide(choice)
    clearDecision()
  }

  if (!decision) return null
  const isRTM = decision.kind === 'RTM'

  return (
    <BottomSheet
      open
      onClose={() => answer(false)}
      dismissible={false}
      title={isRTM ? 'Use a Right-to-Match?' : 'One final raise?'}
    >
      <div className="flex items-center gap-3 mb-4">
        <Avatar name={decision.player.name} size={52} />
        <div className="min-w-0">
          <div className="text-lg font-bold truncate">{decision.player.name}</div>
          <RoleChip role={decision.player.role} overseas={decision.player.is_overseas} />
        </div>
      </div>

      {isRTM ? (
        <>
          <p className="text-sm text-slate-400 mb-4">
            This player was in your 2024 squad. Match the winning bid to take them back — the
            original bidder then gets one raise, and you must pay that price.
          </p>
          <Row label="Match at" value={money(decision.priceLakh)} />
          <Row label="RTM cards left" value={String(decision.rtmCardsRemaining ?? 0)} muted />
        </>
      ) : (
        <>
          <p className="text-sm text-slate-400 mb-4">
            {decision.otherFranchise} played their RTM card. You get one raise — if you take it,
            they must pay the higher price or release the player.
          </p>
          <Row label="Their match" value={money(decision.priceLakh)} muted />
          <Row label="Raise to" value={money(decision.raiseToLakh ?? 0)} />
        </>
      )}

      <div
        className={`text-center text-sm font-bold my-4 tabular-nums ${
          left <= 5 ? 'text-rose-400' : 'text-slate-500'
        }`}
      >
        {left}s to decide
      </div>

      <Button variant="gold" className="w-full h-14 mb-2" onClick={() => answer(true)}>
        {isRTM ? 'Use RTM card' : 'Raise'}
      </Button>
      <Button variant="ghost" className="w-full h-13 py-3.5 mb-2" onClick={() => answer(false)}>
        {isRTM ? 'Let them go' : 'Let it stand'}
      </Button>
    </BottomSheet>
  )
}

function Row({ label, value, muted }: { label: string; value: string; muted?: boolean }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-line/5">
      <span className="text-sm text-slate-400">{label}</span>
      <span className={`font-bold tabular-nums ${muted ? 'text-slate-400' : 'text-lg'}`}>
        {value}
      </span>
    </div>
  )
}
