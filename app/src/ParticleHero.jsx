import { useEffect, useState } from 'react'
import { ParticleNetwork } from '@designcodeio/threeui'

// Ambient masthead field: ThreeUI's ParticleNetwork in light mode, warm-tinted
// and near-transparent — a texture, not a feature. Desktop + motion-safe only.
export default function ParticleHero() {
  const [enabled, setEnabled] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1024px)')
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setEnabled(mq.matches && !motion.matches)
    update()
    mq.addEventListener('change', update)
    motion.addEventListener('change', update)
    return () => {
      mq.removeEventListener('change', update)
      motion.removeEventListener('change', update)
    }
  }, [])

  if (!enabled) return null

  return (
    <div
      aria-hidden="true"
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
        zIndex: 0,
        // warm the library's cool light-ink palette toward the paper ground
        filter: 'sepia(0.32) saturate(0.9) brightness(1.02)',
        opacity: 0.5,
      }}
    >
      <ParticleNetwork
        mode="light"
        density={0.7}
        speed={0.6}
        style={{ width: '100%', height: '100%', background: 'transparent' }}
      />
    </div>
  )
}
