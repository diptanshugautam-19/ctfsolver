"use client"
import { useEffect, useRef } from "react"

export function WandCursor() {
  const ref = useRef<HTMLDivElement>(null)
  const last = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const el = ref.current
    if (!el) return

    let raf = 0
    const pos = { x: window.innerWidth / 2, y: window.innerHeight / 2 }
    const vel = { x: 0, y: 0 }

    const onMove = (e: PointerEvent) => {
      const targetX = e.clientX
      const targetY = e.clientY
      cancelAnimationFrame(raf)
      const tick = () => {
        vel.x += (targetX - pos.x) * 0.2
        vel.y += (targetY - pos.y) * 0.2
        vel.x *= 0.3
        vel.y *= 0.3
        pos.x += vel.x
        pos.y += vel.y
        const angle = Math.atan2(pos.y - last.current.y, pos.x - last.current.x) + Math.PI * 0.05
        el.style.transform = `translate(${pos.x}px, ${pos.y}px) rotate(${angle}rad)`
        last.current = { x: pos.x, y: pos.y }
        if (Math.hypot(targetX - pos.x, targetY - pos.y) > 0.5) {
          raf = requestAnimationFrame(tick)
        }
      }
      raf = requestAnimationFrame(tick)
    }

    window.addEventListener("pointermove", onMove, { passive: true })
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener("pointermove", onMove)
    }
  }, [])

  // CSS-only wand: handle + golden tip glow
  return (
    <div
      ref={ref}
      aria-hidden
      className="wand-pointer fixed left-0 top-0 z-[1000]"
      style={{ transform: "translate(-100px, -100px)" }}
    >
      <div className="relative -translate-x-6 -translate-y-2">
        {/* Handle */}
        <div
          className="h-[3px] w-8 rounded-full"
          style={{
            background:
              "linear-gradient(90deg, color-mix(in oklab, var(--color-secondary) 85%, black 10%), color-mix(in oklab, var(--color-secondary) 65%, black 5%))",
            boxShadow: "0 0 6px color-mix(in oklab, var(--color-secondary) 60%, transparent)",
          }}
        />
        {/* Tip */}
        <div
          className="absolute right-[-8px] top-[-3px] h-2 w-2 rounded-full gold-glow"
          style={{
            background: "var(--color-primary)",
            boxShadow:
              "0 0 8px var(--color-primary), 0 0 16px color-mix(in oklab, var(--color-primary) 80%, transparent)",
          }}
        />
      </div>
    </div>
  )
}
