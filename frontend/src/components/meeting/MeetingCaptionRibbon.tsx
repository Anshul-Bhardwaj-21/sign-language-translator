import { AnimatePresence, motion } from 'framer-motion'

interface MeetingCaptionRibbonProps {
  caption: string
  extraBreathingRoom: boolean
}

export function MeetingCaptionRibbon({ caption, extraBreathingRoom }: MeetingCaptionRibbonProps) {
  return (
    <AnimatePresence>
      {caption !== '' ? (
        <motion.div
          className="meeting-caption-ribbon"
          style={extraBreathingRoom ? { marginBottom: '4rem' } : undefined}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 12 }}
          transition={{ duration: 0.24, ease: 'easeOut' }}
        >
          <span>Live captions</span>
          <strong>{caption}</strong>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
