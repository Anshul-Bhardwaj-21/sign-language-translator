import { useAppContext } from '../contexts/AppContext'

function SettingToggle({ label, description, checked, onChange }: {
  label: string; description?: string; checked: boolean; onChange: (v: boolean) => void
}) {
  return (
    <div className="setting-row">
      <div className="setting-row__copy">
        <strong>{label}</strong>
        {description && <span>{description}</span>}
      </div>
      <div className="setting-row__control">
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            style={{ width: 16, height: 16, accentColor: 'var(--accent-start)' }}
          />
        </label>
      </div>
    </div>
  )
}

export function SettingsPage() {
  const { preferences, updatePreferences } = useAppContext()

  return (
    <div className="settings-page">
      <div className="settings-page__title">Settings</div>
      <p className="settings-page__sub">Meeting defaults and accessibility preferences.</p>

      <div className="settings-section">
        <div className="settings-section__header">Media defaults</div>
        <div className="settings-section__body">
          <SettingToggle
            label="Start with camera enabled"
            checked={preferences.cameraEnabled}
            onChange={(v) => updatePreferences({ cameraEnabled: v })}
          />
          <SettingToggle
            label="Start with microphone enabled"
            checked={preferences.micEnabled}
            onChange={(v) => updatePreferences({ micEnabled: v })}
          />
          <div className="setting-row">
            <div className="setting-row__copy">
              <strong>Preferred layout</strong>
              <span>Default video grid mode when entering a room</span>
            </div>
            <div className="setting-row__control">
              <select
                value={preferences.preferredLayout}
                onChange={(e) => updatePreferences({ preferredLayout: e.target.value === 'grid' ? 'grid' : 'focus' })}
              >
                <option value="focus">Focus view</option>
                <option value="grid">Grid view</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="settings-section">
        <div className="settings-section__header">Translation & accessibility</div>
        <div className="settings-section__body">
          <SettingToggle
            label="Enable sign interpretation on join"
            description="Starts the inference pipeline when you enter a room"
            checked={preferences.translationEnabled}
            onChange={(v) => updatePreferences({ translationEnabled: v })}
          />
          <SettingToggle
            label="Auto-speak confirmed captions"
            description="Uses Web Speech API to read captions aloud"
            checked={preferences.autoSpeakCaptions}
            onChange={(v) => updatePreferences({ autoSpeakCaptions: v })}
          />
          <SettingToggle
            label="Accessibility mode by default"
            description="Enables hand tracking and visual guidance overlays"
            checked={preferences.accessibilityMode}
            onChange={(v) => updatePreferences({ accessibilityMode: v })}
          />
          <SettingToggle
            label="Show vision assist overlays"
            description="Renders hand landmarks and face frame on your local tile"
            checked={preferences.showVisionOverlay}
            onChange={(v) => updatePreferences({ showVisionOverlay: v })}
          />
          <div className="setting-row">
            <div className="setting-row__copy">
              <strong>Frame capture interval</strong>
              <span>{preferences.captureIntervalMs} ms between predictions</span>
            </div>
            <div className="setting-row__control">
              <input
                type="range"
                min="500"
                max="2000"
                step="100"
                value={preferences.captureIntervalMs}
                onChange={(e) => updatePreferences({ captureIntervalMs: Number(e.target.value) })}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
