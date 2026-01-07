import time
from pathlib import Path

from faster_whisper import WhisperModel


class STTDriver:
    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        print(f"[STT] Loading model: {model_size} on {device}/{compute_type}")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, wav_path: Path) -> str:
        start = time.time()
        segments, _ = self.model.transcribe(str(wav_path))
        text = "".join(seg.text for seg in segments).strip()
        elapsed = time.time() - start
        print(f"[STT] Took {elapsed:.2f}s, text='{text}'")
        return text
