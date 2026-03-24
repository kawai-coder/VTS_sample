import argparse
import json
import time
from pathlib import Path

from audio_listener import AudioListener, list_input_devices
from config import (
    COOLDOWN_AFTER_PLAY_SEC,
    EMO_TO_HOTKEY,
    END_TRIGGER_FRAMES,
    MAX_UTTERANCE_SEC,
    MIC_DEVICE,
    POSE_TO_HOTKEY,
    RUNS_DIR,
    SAMPLE_RATE,
    START_TRIGGER_FRAMES,
    VAD_MODE,
    FRAME_MS,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_MODEL,
)
from llm_driver import LLMDriver
from stt_driver import STTDriver
from tts_driver import TTSDriver
from vts_client import VTSClient


def save_debug(runs_dir: Path, stem: str, text: str) -> None:
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{stem}.txt"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="save wav+stt+llm into runs/")
    parser.add_argument("--list-devices", action="store_true")
    args = parser.parse_args()

    if args.list_devices:
        list_input_devices()
        return

    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    vts = VTSClient()
    try:
        vts.connect()
    except Exception as exc:
        print(f"[VTS] Connection failed: {exc}")

    llm = LLMDriver()
    stt = STTDriver(WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE)
    tts = TTSDriver(RUNS_DIR)
    listener = AudioListener(
        sample_rate=SAMPLE_RATE,
        frame_ms=FRAME_MS,
        vad_mode=VAD_MODE,
        start_trigger_frames=START_TRIGGER_FRAMES,
        end_trigger_frames=END_TRIGGER_FRAMES,
        max_utterance_sec=MAX_UTTERANCE_SEC,
        runs_dir=RUNS_DIR,
        device=MIC_DEVICE,
    )

    last_emo = "neutral"
    cooldown_until = 0.0

    print("[Main] Start listening... Ctrl+C to exit.")
    try:
        while True:
            if time.time() < cooldown_until:
                time.sleep(0.05)
                continue
            try:
                wav_path = listener.listen_utterance()
            except Exception as exc:
                print(f"[Audio] Listen failed: {exc}")
                continue
            if not wav_path:
                continue

            try:
                text = stt.transcribe(wav_path)
            except Exception as exc:
                print(f"[STT] Failed: {exc}")
                continue

            if not text:
                print("[STT] Empty text, skip")
                continue

            if args.debug:
                save_debug(RUNS_DIR, wav_path.stem + "_stt", text)

            try:
                llm_json = llm.generate(text)
                print(f"[LLM] Output: {llm_json}")
            except Exception as exc:
                print(f"[LLM] Failed: {exc}")
                llm_json = {
                    "reply": text,
                    "emo": {"label": "neutral", "intensity": 0.3},
                    "pose": "talk",
                }

            if args.debug:
                save_debug(RUNS_DIR, wav_path.stem + "_llm", json.dumps(llm_json, ensure_ascii=False, indent=2))

            emo = llm_json.get("emo", {})
            emo_label = emo.get("label", "neutral")
            emo_intensity = float(emo.get("intensity", 0.3))
            pose = llm_json.get("pose", "talk")

            if emo_intensity < 0.4:
                emo_label = last_emo
            last_emo = emo_label

            try:
                if pose in POSE_TO_HOTKEY:
                    vts.trigger_hotkey(POSE_TO_HOTKEY[pose])
                if emo_label in EMO_TO_HOTKEY:
                    vts.trigger_hotkey(EMO_TO_HOTKEY[emo_label])
            except Exception as exc:
                print(f"[VTS] Trigger failed: {exc}")

            reply = llm_json.get("reply", "")
            try:
                listener.stop()
                wav_tts = tts.synthesize(reply)
                tts.play(wav_tts)
            except Exception as exc:
                print(f"[TTS] Failed: {exc}")
            finally:
                try:
                    listener.start()
                except Exception as exc:
                    print(f"[Audio] Restart failed: {exc}")

            try:
                if "idle" in POSE_TO_HOTKEY:
                    vts.trigger_hotkey(POSE_TO_HOTKEY["idle"])
                if "neutral" in EMO_TO_HOTKEY:
                    vts.trigger_hotkey(EMO_TO_HOTKEY["neutral"])
            except Exception as exc:
                print(f"[VTS] Idle trigger failed: {exc}")

            cooldown_until = time.time() + COOLDOWN_AFTER_PLAY_SEC
    except KeyboardInterrupt:
        print("[Main] Exiting...")
    finally:
        listener.stop()
        vts.close()


if __name__ == "__main__":
    main()
