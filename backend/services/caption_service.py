from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from time import monotonic
from typing import Deque


@dataclass
class CaptionSession:
    live_caption: str = ""
    last_committed_label: str = ""
    last_commit_at: float = 0.0
    history: Deque[str] = field(default_factory=lambda: deque(maxlen=10))


@dataclass
class CaptionSnapshot:
    live_caption: str
    confirmed_caption: str | None
    history: list[str]


class CaptionService:
    def __init__(self, cooldown_seconds: float = 1.3) -> None:
        self._cooldown_seconds = cooldown_seconds
        self._sessions: dict[str, CaptionSession] = {}

    def update(
        self,
        session_key: str,
        label: str,
        confidence: float,
        stable: bool,
    ) -> CaptionSnapshot:
        session = self._sessions.setdefault(session_key, CaptionSession())
        confirmed_caption: str | None = None

        if label == "idle" or confidence <= 0:
            session.live_caption = ""
            return CaptionSnapshot("", None, list(session.history))

        session.live_caption = label

        now = monotonic()
        ready_to_commit = stable or confidence >= 0.82
        not_duplicate = label != session.last_committed_label or (now - session.last_commit_at) >= self._cooldown_seconds

        if ready_to_commit and not_duplicate:
            session.history.append(label)
            session.last_committed_label = label
            session.last_commit_at = now
            confirmed_caption = label

        return CaptionSnapshot(session.live_caption, confirmed_caption, list(session.history))

