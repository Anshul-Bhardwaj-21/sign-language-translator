# SignBridge

**Real-time video meeting platform with sign-language intelligence and live captions.**

Multiple participants join a room, communicate via WebRTC audio/video, and one participant can enable Accessibility Mode — their camera frames are analyzed by a sign-language model, the detected sign becomes a live caption for everyone in the room, and the receiver hears it spoken aloud via browser TTS.

---

## Problem Statement

Most meeting tools treat accessibility as an afterthought. Mixed groups — where some participants use sign language — have no seamless way to communicate in real time. SignBridge makes sign-language interpretation a first-class feature of the meeting experience, not a separate tool.

---

## Architecture

```
Browser A (signer)          Browser B (receiver)
    │                              │
    │  WebRTC audio/video ─────────┤
    │  WebSocket signaling ─────────┤
    │                              │
    └──► FastAPI backend ◄──────────┘
              │
              ├── Room manager (in-memory)
              ├── WebRTC signaling relay
              ├── Chat relay
              ├── Caption relay
              └── Sign-language inference
                      │
                      ├── HeuristicSignModelEngine (always ready)
                      ├── LocalSignModelEngine (after training)
                      └── CloudAIEngine (optional)
```

---

## Repo Structure

```
/
├── backend/
│   ├── main.py                  # Entrypoint — run this
│   ├── api/routes/              # health, rooms, predict
│   ├── realtime/                # WebSocket signaling + manager
│   ├── services/                # room, model, caption services
│   ├── ml/engines/              # heuristic, local, cloud engines
│   ├── schemas/                 # Pydantic request/response models
│   ├── core/                    # config, errors, logging
│   ├── training/                # model training scaffold
│   ├── inference_model.py       # LocalModelBundle (PyTorch)
│   └── .env.example             # copy to .env
├── frontend/
│   ├── src/
│   │   ├── pages/               # Landing, Login, Dashboard, Lobby, Room
│   │   ├── hooks/               # useRoomSession (WebRTC + WS)
│   │   ├── components/          # MediaTile, VisionAssistOverlay, etc.
│   │   ├── contexts/            # AppContext (auth + preferences)
│   │   └── services/api.ts      # REST + ICE server fetch
│   └── .env.example             # copy to .env
├── models/                      # place trained weights here
├── README.md
└── TODO.md
```

---

## Setup — Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- pip

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# Copy env file
cp .env.example .env

# Start backend
python main.py
```

Backend runs at `http://localhost:8001`.

Verify: `curl http://localhost:8001/health`

### 2. Frontend

```bash
cd frontend
npm install

# Copy env file
cp .env.example .env

# Start dev server
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## Multi-Computer Demo (LAN)

To connect two computers on the same network:

1. Find your machine's local IP:
   ```bash
   # Windows
   ipconfig
   # macOS / Linux
   ifconfig | grep inet
   ```

2. Update `backend/.env`:
   ```
   HOST=0.0.0.0
   CORS_ORIGINS=http://192.168.1.10:5173,http://localhost:5173
   ```

3. Update `frontend/.env` on **both** machines:
   ```
   VITE_API_URL=http://192.168.1.10:8001
   VITE_WS_URL=ws://192.168.1.10:8001
   ```
   Replace `192.168.1.10` with the host machine's actual IP.

4. Start backend on the host machine, frontend on both.

5. Both users open `http://192.168.1.10:5173`, sign in, and join the same room code.

> **Note:** Same-network (LAN) connections work with STUN only. Cross-network connections (different ISPs) require a TURN server. See `backend/.env.example` for TURN configuration.

---

## Room Join Demo

1. **User A** opens the app → Sign in → Dashboard → **Create room**
2. A 6-character room code appears (e.g. `ABC123`)
3. **User B** opens the app on another computer → Sign in → Dashboard → Enter `ABC123` → **Join**
4. Both users are now in the same video call
5. **User A** clicks **Accessibility** in the toolbar to enable sign-language mode
6. User A signs in front of their camera — detected signs appear as captions for both users
7. **User B** hears the caption spoken aloud via browser TTS

---

## Sign-Language Model

### Current state (fallback mode)

The heuristic engine is always active. It uses hand landmark geometry to classify basic signs:
- `hello`, `yes`, `no`, `help`, `thanks`, `please`, `peace`, `ready`, `idle`

This is demo-stable and works without any trained weights.

### Enabling fallback mode explicitly

In `backend/.env`:
```
USE_FALLBACK_SIGN_MODEL=1
```

### Plugging in trained weights

After training your model:

1. Place model files in `backend/artifacts/models/local_sign_model/`:
   ```
   model.pt        # PyTorch state dict
   labels.json     # ["hello", "yes", "no", ...]
   metadata.json   # {"num_classes": 10}
   ```

2. Update `backend/.env`:
   ```
   MODEL_ENGINE=local
   USE_FALLBACK_SIGN_MODEL=0
   ```

3. Restart the backend — it loads the model automatically.

The model architecture is MobileNetV3-Small. See `backend/training/` for the training scaffold and `backend/train.py` to run training.

---

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Backend status + engine info |
| GET | `/ice-servers` | WebRTC ICE server config |
| POST | `/rooms` | Create a room |
| POST | `/rooms/{id}/join` | Join a room |
| GET | `/rooms/{id}` | Get room snapshot |
| POST | `/predict` | Sign-language inference |
| WS | `/ws/rooms/{id}` | Realtime signaling |

---

## Keyboard Shortcuts (in-call)

| Key | Action |
|-----|--------|
| `M` | Mute / unmute |
| `V` | Camera on / off |
| `A` | Toggle accessibility mode |
| `Ctrl+C` | Clear captions |
| `P` | Participants panel |
| `T` | Transcript panel |
| `H` / `Shift+?` | Shortcuts help |
| `Esc` | Close panel |

---

## Known Limitations

- **TURN server not included** — cross-network connections (different ISPs) may fail without a TURN server. Configure `TURN_URL`, `TURN_USERNAME`, `TURN_PASSWORD` in `backend/.env`.
- **In-memory room state** — rooms are lost on backend restart. Add a database for persistence.
- **No authentication** — session identity is local only. Add proper auth before production.
- **Single-region** — no geographic distribution. Add a CDN and regional backends for scale.
- **Model not trained** — heuristic engine recognizes ~8 signs. Train on a full dataset for production accuracy.

---

## Hackathon Demo Script

```
1. Open two browser windows (or two computers on same network)
2. Window 1: Sign in as "Alice" → Create room → note the code
3. Window 2: Sign in as "Bob" → Join with the code
4. Both see each other's video
5. Alice: click "Accessibility" button in toolbar
6. Alice: make a sign (open hand = "hello", fist = "yes")
7. Bob: sees the caption appear at the bottom of the screen
8. Bob: hears the caption spoken aloud
9. Both: use chat panel as fallback
10. Show the /health endpoint to demonstrate backend is live
```

---

## Screenshots

> Add screenshots to `assets/screenshots/` after running the demo.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Real-time | WebRTC (native), WebSocket |
| Backend | FastAPI, Uvicorn, Python 3.11 |
| ML | PyTorch, MobileNetV3, MediaPipe |
| Inference | Heuristic (live) → Local model (post-training) |
| TTS | Browser SpeechSynthesis API |
| Deploy | Netlify (frontend) + Railway (backend) |
