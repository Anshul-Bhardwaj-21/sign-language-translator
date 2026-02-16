# 🚨 CRITICAL FIXES REQUIRED - ACTION NEEDED NOW

## ⚠️ YOUR APP IS CURRENTLY BROKEN

These issues will prevent your application from running correctly. Fix them immediately before proceeding with any other work.

---

## 🔴 ISSUE #1: NumPy/MediaPipe Incompatibility (BLOCKING)

### Problem:
Your `requirements.txt` specifies Python 3.14 with NumPy 2.x, but MediaPipe 0.10.32 **DOES NOT WORK** with NumPy 2.x.

### Current State:
```python
# requirements.txt
numpy>=2.0.0  # Python 3.14 requirement
mediapipe==0.10.32  # Requires NumPy <2.0
```

### Error You'll See:
```
ImportError: numpy.core.multiarray failed to import
ModuleNotFoundError: No module named 'numpy.core.multiarray'
```

### FIX NOW:

**Option A: Downgrade Python (RECOMMENDED)**
```bash
# 1. Update requirements.txt
numpy>=1.23.0,<2.0.0
mediapipe==0.10.32

# 2. Use Python 3.11 instead of 3.14
python --version  # Should show 3.11.x

# 3. Recreate virtual environment
deactivate
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Option B: Wait for MediaPipe Update (NOT AVAILABLE YET)**
```
MediaPipe 0.11+ will support NumPy 2.x
Currently not released - DO NOT USE THIS OPTION
```

### Verification:
```bash
python -c "import mediapipe; import numpy; print('✅ Success')"
```

---

## 🔴 ISSUE #2: Memory Leak in Frame Capture (CRASHES BROWSER)

### Problem:
`FrameCaptureManager` never cancels `requestAnimationFrame`, causing memory to grow until browser crashes.

### Current Code (BROKEN):
```typescript
// frontend/src/services/FrameCaptureManager.ts
const processLoop = async () => {
  if (!this.isRunning) return;  // ❌ RAF already scheduled
  requestAnimationFrame(processLoop);  // ❌ No way to cancel
};
```

### FIX NOW:

Replace the entire `FrameCaptureManager.ts` file with this:

```typescript
import { api, MLResult } from './api';

export class FrameCaptureManager {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private targetFPS: number = 10;
  private lastCaptureTime: number = 0;
  private isProcessing: boolean = false;
  private userId: string;
  private sessionId: string;
  private isRunning: boolean = false;
  private rafId: number | null = null;  // ✅ ADDED

  constructor(userId: string, sessionId: string) {
    this.canvas = document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d')!;
    this.userId = userId;
    this.sessionId = sessionId;
  }

  setTargetFPS(fps: number): void {
    this.targetFPS = Math.max(1, Math.min(30, fps));
  }

  private captureFrame(videoElement: HTMLVideoElement): string | null {
    const now = Date.now();
    const interval = 1000 / this.targetFPS;

    if (now - this.lastCaptureTime < interval) {
      return null;
    }

    if (this.isProcessing) {
      return null;
    }

    this.lastCaptureTime = now;

    this.canvas.width = 640;
    this.canvas.height = 480;
    this.ctx.drawImage(videoElement, 0, 0, 640, 480);

    return this.canvas.toDataURL('image/jpeg', 0.8);
  }

  async processFrame(videoElement: HTMLVideoElement): Promise<MLResult | null> {
    const frame = this.captureFrame(videoElement);
    if (!frame) {
      return null;
    }

    this.isProcessing = true;

    try {
      const result = await api.processFrame(frame, this.userId, this.sessionId);
      return result;
    } finally {
      this.isProcessing = false;
    }
  }

  startProcessing(
    videoElement: HTMLVideoElement,
    onResult: (result: MLResult) => void
  ): void {
    this.isRunning = true;

    const processLoop = async () => {
      if (!this.isRunning) {
        this.rafId = null;  // ✅ FIXED
        return;
      }

      const result = await this.processFrame(videoElement);
      if (result) {
        onResult(result);
      }

      this.rafId = requestAnimationFrame(processLoop);  // ✅ FIXED
    };

    processLoop();
  }

  stopProcessing(): void {
    this.isRunning = false;
    
    // ✅ ADDED: Cancel animation frame
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    
    // ✅ ADDED: Clean up canvas
    this.canvas.width = 0;
    this.canvas.height = 0;
  }
}
```

### Verification:
1. Open browser DevTools → Performance tab
2. Start recording
3. Enable accessibility mode for 2 minutes
4. Stop recording
5. Check memory graph - should be flat, not growing

---

## 🔴 ISSUE #3: AbortSignal.timeout() Browser Compatibility

### Problem:
`AbortSignal.timeout()` doesn't work in Safari < 16, older Chrome/Firefox.

### Current Code (BROKEN):
```typescript
// frontend/src/services/api.ts line 68
signal: AbortSignal.timeout(5000)
```

### FIX NOW:

Replace the `processFrame` method in `frontend/src/services/api.ts`:

```typescript
async processFrame(frame: string, userId: string, sessionId: string): Promise<MLResult> {
  // ✅ FIXED: Manual timeout implementation
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(`${API_BASE_URL}/api/ml/process-frame`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        frame,
        user_id: userId,
        session_id: sessionId,
        timestamp: Date.now() / 1000
      }),
      signal: controller.signal  // ✅ Use manual controller
    });

    clearTimeout(timeoutId);  // ✅ Clear timeout on success

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);  // ✅ Clear timeout on error
    
    console.error('ML processing failed:', error);
    return {
      success: false,
      hand_detected: false,
      gesture: 'none',
      confidence: 0,
      caption: '',
      movement_state: 'error',
      processing_time_ms: 0,
      error: error instanceof Error ? error.message : 'Unknown error',
      fallback_mode: 'text_only'
    };
  }
}
```

### Verification:
Test in Safari or use BrowserStack to verify compatibility.

---

## 🟡 ISSUE #4: Camera Race Condition

### Problem:
Rapidly toggling camera can open multiple streams, causing camera to stay locked.

### FIX NOW:

Add this to `frontend/src/pages/VideoCallPage.tsx` at the top of the component:

```typescript
// Add this ref near other refs
const initializingRef = useRef(false);

// Update initializeCamera function
const initializeCamera = useCallback(async () => {
  if (!cameraEnabled || initializingRef.current) return;  // ✅ ADDED lock check
  
  initializingRef.current = true;  // ✅ ADDED lock
  setIsLoadingCamera(true);
  setCameraError('');

  const constraints = [
    // ... existing constraints
  ];

  for (const constraint of constraints) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia(constraint);
      setLocalStream(stream);
      
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
        await localVideoRef.current.play();
      }
      
      setIsLoadingCamera(false);
      initializingRef.current = false;  // ✅ ADDED unlock
      return;
    } catch (err) {
      console.log('Camera attempt failed:', err);
      continue;
    }
  }
  
  setCameraError('Could not access camera...');
  setIsLoadingCamera(false);
  setCameraEnabled(false);
  initializingRef.current = false;  // ✅ ADDED unlock
}, [cameraEnabled]);
```

---

## 🟡 ISSUE #5: Pydantic V2 Compatibility

### Problem:
Using deprecated `@validator` decorator from Pydantic v1.

### FIX NOW:

Update `backend/enhanced_server.py` line 50:

```python
# BEFORE (DEPRECATED):
from pydantic import BaseModel, validator

class FrameRequest(BaseModel):
    # ... fields
    
    @validator('frame')
    def validate_frame(cls, v):
        # ...

# AFTER (FIXED):
from pydantic import BaseModel, field_validator

class FrameRequest(BaseModel):
    frame: str
    user_id: str
    session_id: str
    timestamp: float
    
    @field_validator('frame')  # ✅ FIXED
    @classmethod  # ✅ ADDED
    def validate_frame(cls, v: str) -> str:  # ✅ ADDED type hints
        if not v.startswith('data:image/jpeg;base64,'):
            raise ValueError('Invalid frame format')
        if len(v) > 2_000_000:
            raise ValueError('Frame too large')
        return v
```

---

## 🟡 ISSUE #6: CORS Security

### Problem:
CORS allows all methods and headers, security risk.

### FIX NOW:

Update both `backend/server.py` and `backend/enhanced_server.py`:

```python
# BEFORE (INSECURE):
app.add_middleware(
    CORSMiddleware,
    allow_origins=[...],
    allow_credentials=True,
    allow_methods=["*"],  # ❌ Too permissive
    allow_headers=["*"],  # ❌ Too permissive
)

# AFTER (SECURE):
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # ✅ Explicit only
    allow_headers=["Content-Type", "Authorization"],  # ✅ Explicit only
    max_age=3600,  # ✅ Cache preflight
)
```

---

## ✅ VERIFICATION CHECKLIST

After applying all fixes, verify:

- [ ] Python imports work: `python -c "import mediapipe; import numpy; print('OK')"`
- [ ] Backend starts: `python backend/server.py` (no errors)
- [ ] Frontend builds: `cd frontend && npm run build` (no errors)
- [ ] Camera toggles work (on/off/on/off) without getting stuck
- [ ] Memory stays stable (check DevTools Performance tab)
- [ ] Works in Safari (test or use BrowserStack)
- [ ] No deprecation warnings in console

---

## 🚀 QUICK FIX SCRIPT

Run this to apply all fixes automatically:

```bash
#!/bin/bash

echo "🔧 Applying critical fixes..."

# Fix 1: Update requirements.txt
sed -i 's/numpy>=2.0.0/numpy>=1.23.0,<2.0.0/' requirements.txt
echo "✅ Fixed NumPy version"

# Fix 2-6: Manual code changes required
echo "⚠️  Manual fixes required for:"
echo "   - FrameCaptureManager.ts (memory leak)"
echo "   - api.ts (AbortSignal compatibility)"
echo "   - VideoCallPage.tsx (camera race condition)"
echo "   - enhanced_server.py (Pydantic v2)"
echo "   - server.py + enhanced_server.py (CORS)"
echo ""
echo "📖 See CRITICAL_FIXES_REQUIRED.md for detailed instructions"

# Reinstall dependencies
echo "📦 Reinstalling Python dependencies..."
pip install -r requirements.txt

echo "✅ Critical fixes applied!"
echo "⚠️  Remember to apply manual code changes!"
```

---

## 📞 NEED HELP?

If you encounter issues applying these fixes:

1. Check the full audit: `COMPREHENSIVE_CODE_AUDIT.md`
2. Review error messages carefully
3. Test each fix individually
4. Verify with the checklist above

**DO NOT PROCEED** with other development until these critical issues are fixed!

---

**Last Updated:** $(date)
**Priority:** 🔴 CRITICAL - FIX IMMEDIATELY
