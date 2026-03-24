import time
import wave
from collections import deque
from pathlib import Path
from typing import Optional

import sounddevice as sd
import webrtcvad


def list_input_devices() -> None:
    print("[Audio] Available input devices:")
    for idx, dev in enumerate(sd.query_devices()):
        if dev.get("max_input_channels", 0) > 0:
            print(f"  {idx}: {dev['name']}")


class AudioListener:
    def __init__(
        self,
        sample_rate: int,
        frame_ms: int,
        vad_mode: int,
        start_trigger_frames: int,
        end_trigger_frames: int,
        max_utterance_sec: int,
        runs_dir: Path,
        device: Optional[int] = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frame_samples = int(sample_rate * frame_ms / 1000)
        self.vad = webrtcvad.Vad(vad_mode)
        self.start_trigger_frames = start_trigger_frames
        self.end_trigger_frames = end_trigger_frames
        self.max_utterance_sec = max_utterance_sec
        self.device = device
        self.runs_dir = runs_dir
        self.stream: Optional[sd.RawInputStream] = None

    def start(self) -> None:
        if self.stream is not None:
            return
        self.stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=self.frame_samples,
            dtype="int16",
            channels=1,
            device=self.device,
        )
        self.stream.start()
        print("[Audio] Input stream started")

    def stop(self) -> None:
        if self.stream is None:
            return
        self.stream.stop()
        self.stream.close()
        self.stream = None
        print("[Audio] Input stream stopped")

    def _write_wav(self, pcm_frames: list[bytes]) -> Path:
        ts = int(time.time() * 1000)
        wav_path = self.runs_dir / f"utterance_{ts}.wav"
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(pcm_frames))
        return wav_path

    def listen_utterance(self) -> Optional[Path]:
        if self.stream is None:
            self.start()
        assert self.stream is not None

        prebuffer: deque[bytes] = deque(maxlen=self.start_trigger_frames)
        speech_count = 0
        nonspeech_count = 0
        in_speech = False
        utterance_frames: list[bytes] = []
        utterance_start = None

        while True:
            data, _ = self.stream.read(self.frame_samples)
            is_speech = self.vad.is_speech(data, self.sample_rate)

            if not in_speech:
                prebuffer.append(data)
                if is_speech:
                    speech_count += 1
                else:
                    speech_count = 0
                if speech_count >= self.start_trigger_frames:
                    in_speech = True
                    utterance_frames = list(prebuffer)
                    utterance_start = time.time()
                    print("[VAD] Speech start")
            else:
                utterance_frames.append(data)
                if is_speech:
                    nonspeech_count = 0
                else:
                    nonspeech_count += 1

                elapsed = time.time() - (utterance_start or time.time())
                if nonspeech_count >= self.end_trigger_frames or elapsed >= self.max_utterance_sec:
                    print("[VAD] Speech end")
                    if utterance_frames:
                        return self._write_wav(utterance_frames)
                    return None
