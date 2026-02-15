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
      if (!this.isRunning) return;

      const result = await this.processFrame(videoElement);
      if (result) {
        onResult(result);
      }

      requestAnimationFrame(processLoop);
    };

    processLoop();
  }

  stopProcessing(): void {
    this.isRunning = false;
  }
}
