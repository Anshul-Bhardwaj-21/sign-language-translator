# TODO — SignBridge

Actionable future work, in priority order.

## High priority (before production)

- [ ] Train real sign-language model on full ASL/ISL dataset
- [ ] Replace heuristic engine with trained LocalSignModelEngine
- [ ] Deploy TURN server (coturn or Twilio) for cross-network reliability
- [ ] Add proper authentication (JWT or OAuth)
- [ ] Add database persistence for rooms, chat history, and session logs

## Medium priority

- [ ] Add multilingual caption support (translate detected signs to multiple languages)
- [ ] Optimize inference latency (target < 200ms per frame)
- [ ] Add screen share support (getDisplayMedia)
- [ ] Add local recording (MediaRecorder — scaffold exists in useLocalRecording)
- [ ] Add participant analytics dashboard (speaking time, engagement)
- [ ] Add unread message indicator for chat panel

## Low priority / post-MVP

- [ ] Profile avatars and display picture upload
- [ ] Conversation history persistence and export
- [ ] Advanced admin controls (mute all, remove participant)
- [ ] Mobile-optimized layout
- [ ] End-to-end encryption for media streams
- [ ] Geographic distribution (regional backends)
- [ ] Automated CI/CD pipeline for model retraining
