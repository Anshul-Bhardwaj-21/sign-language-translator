import { AnimatePresence, motion } from 'framer-motion'
import type { ReactionBurst } from '../../types/app'

interface ReactionBurstLayerProps {
  reactionBursts: ReactionBurst[]
}

export function ReactionBurstLayer({ reactionBursts }: ReactionBurstLayerProps) {
  return (
    <div
      className="reaction-burst-layer"
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
      }}
    >
      <AnimatePresence>
        {reactionBursts.map((burst) => (
          <motion.div
            key={burst.id}
            initial={{ opacity: 0, y: 0, scale: 0.6 }}
            animate={{ opacity: 1, y: -80, scale: 1 }}
            exit={{ opacity: 0, y: -140, scale: 0.8 }}
            transition={{ duration: 2.2, ease: 'easeOut' }}
            style={{
              position: 'absolute',
              bottom: 16,
              fontSize: '2rem',
              lineHeight: 1,
              userSelect: 'none',
            }}
            aria-hidden="true"
          >
            {burst.emoji}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
