import { AnimatePresence, motion } from 'framer-motion'
import type { ChatPreviewBubble as ChatPreviewBubbleType } from '../../types/app'

interface ChatPreviewBubbleProps {
  bubble: ChatPreviewBubbleType | null
  visible: boolean
}

export function ChatPreviewBubble({ bubble, visible }: ChatPreviewBubbleProps) {
  return (
    <AnimatePresence>
      {visible && bubble !== null ? (
        <motion.div
          key={bubble.id}
          className="tile-chat-preview"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
        >
          <span className="tile-chat-preview__name">{bubble.displayName}</span>
          <span className="tile-chat-preview__message">{bubble.message}</span>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
