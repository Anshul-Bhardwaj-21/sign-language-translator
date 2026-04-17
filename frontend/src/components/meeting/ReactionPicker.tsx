import { AnimatePresence, motion } from 'framer-motion'

export interface ReactionOption {
  emoji: string
  label: string
}

interface ReactionPickerProps {
  open: boolean
  options: ReactionOption[]
  onSelect: (option: ReactionOption) => void
}

export function ReactionPicker({ open, options, onSelect }: ReactionPickerProps) {
  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="reaction-picker"
          initial={{ opacity: 0, y: 16, scale: 0.94 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 12, scale: 0.97 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
        >
          {options.map((option) => (
            <button key={option.label} type="button" className="reaction-picker__button" onClick={() => onSelect(option)}>
              <span className="reaction-picker__emoji" aria-hidden="true">
                {option.emoji}
              </span>
              <span>{option.label}</span>
            </button>
          ))}
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
