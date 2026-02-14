"""Collect labeled landmark sequences from webcam for model training."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import List, Optional

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.append(str(APP_ROOT))

from camera.camera import create_camera_manager  # noqa: E402
from inference.hand_detector import create_hand_detector  # noqa: E402
from inference.movement_tracker import MovementTracker  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect hand landmark sequences.")
    parser.add_argument("--label", required=True, help="Class label to record (example: HELLO)")
    parser.add_argument("--samples", type=int, default=30, help="How many samples to collect")
    parser.add_argument("--frames", type=int, default=24, help="Frames per sample")
    parser.add_argument("--signer-id", default="signer_01", help="Signer identifier")
    parser.add_argument("--camera-index", type=int, default=0, help="Camera index")
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "ml" / "datasets" / "raw"),
        help="Output dataset root",
    )
    return parser.parse_args()


def save_sample(
    output_dir: Path,
    label: str,
    signer_id: str,
    sequence: List,
    handedness: Optional[str],
    target_frames: int,
) -> Path:
    label_dir = output_dir / label
    label_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    file_path = label_dir / f"{timestamp}.json"

    payload = {
        "label": label,
        "signer_id": signer_id,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_frames": target_frames,
        "captured_frames": len(sequence),
        "handedness": handedness,
        "landmarks": sequence,
    }

    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return file_path


def put_text(frame_bgr, text: str, y: int, color=(255, 255, 255)) -> None:
    cv2.putText(frame_bgr, text, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)

    if args.samples <= 0 or args.frames <= 1:
        print("ERROR: --samples must be > 0 and --frames must be > 1")
        return 1

    camera = create_camera_manager(
        camera_index=args.camera_index,
        width=960,
        height=540,
        target_fps=24,
    )
    ok, message = camera.open()
    if not ok:
        print(f"ERROR: {message}")
        return 1

    try:
        detector = create_hand_detector(max_num_hands=1)
    except Exception as exc:
        camera.release()
        print(f"ERROR: Failed to initialize hand detector: {exc}")
        return 1

    tracker = MovementTracker()

    saved = 0
    recording = False
    sequence: List = []
    handedness: Optional[str] = None

    print("Instructions:")
    print("- Press 'r' to start recording a sample")
    print("- Press 'c' to cancel current recording")
    print("- Press 'q' to quit")

    try:
        while saved < args.samples:
            ok, frame_rgb, error = camera.read_frame()
            if not ok or frame_rgb is None:
                print(f"WARNING: {error}")
                continue

            detection = detector.detect(frame_rgb, draw_landmarks=True)
            preview_rgb = detection.frame_with_landmarks if detection.frame_with_landmarks is not None else frame_rgb
            movement = tracker.update(detection.primary_landmarks if detection.hand_detected else None)

            if recording and detection.hand_detected and detection.primary_landmarks is not None:
                sequence.append(detection.primary_landmarks)
                handedness = detection.handedness or handedness

                if len(sequence) >= args.frames:
                    path = save_sample(
                        output_dir=output_dir,
                        label=args.label,
                        signer_id=args.signer_id,
                        sequence=sequence,
                        handedness=handedness,
                        target_frames=args.frames,
                    )
                    saved += 1
                    print(f"Saved sample {saved}/{args.samples}: {path}")
                    recording = False
                    sequence = []
                    handedness = None

            preview_bgr = cv2.cvtColor(preview_rgb, cv2.COLOR_RGB2BGR)
            put_text(preview_bgr, f"Label: {args.label}", 24, (50, 220, 50))
            put_text(preview_bgr, f"Saved: {saved}/{args.samples}", 48)
            put_text(preview_bgr, f"Hand: {'Yes' if detection.hand_detected else 'No'}", 72)
            put_text(preview_bgr, f"Movement: {movement.state}", 96)
            if recording:
                put_text(preview_bgr, f"Recording... {len(sequence)}/{args.frames}", 120, (0, 220, 255))
            else:
                put_text(preview_bgr, "Press 'r' to record next sample", 120, (0, 220, 255))

            cv2.imshow("Landmark Collection", preview_bgr)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key == ord("r") and not recording:
                recording = True
                sequence = []
                handedness = None
            if key == ord("c") and recording:
                recording = False
                sequence = []
                handedness = None

        print(f"Collection finished: {saved} samples saved for label '{args.label}'.")
        return 0

    finally:
        camera.release()
        detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    raise SystemExit(main())
