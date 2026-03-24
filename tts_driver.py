import asyncio
import time
from pathlib import Path

import edge_tts
import sounddevice as sd
import soundfile as sf

from config import TTS_FORMAT, TTS_VOICE


class TTSDriver:
    def __init__(self, runs_dir: Path) -> None:
        self.runs_dir = runs_dir

    async def _synthesize_async(self, text: str, wav_path: Path) -> None:
        communicate = edge_tts.Communicate(text=text, voice=TTS_VOICE, rate="0%", volume="0%")
        await communicate.save(str(wav_path), output_format=TTS_FORMAT)

    def synthesize(self, text: str) -> Path:
        ts = int(time.time() * 1000)
        wav_path = self.runs_dir / f"tts_{ts}.wav"
        asyncio.run(self._synthesize_async(text, wav_path))
        print(f"[TTS] Generated: {wav_path}")
        return wav_path

    def play(self, wav_path: Path) -> float:
        data, rate = sf.read(str(wav_path), dtype="float32")
        start = time.time()
        sd.play(data, rate)
        sd.wait()
        duration = time.time() - start
        print(f"[TTS] Played in {duration:.2f}s")
        return duration
