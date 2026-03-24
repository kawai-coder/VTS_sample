from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
RUNS_DIR = BASE_DIR / "runs"
TOKEN_PATH = BASE_DIR / "vts_token.json"

# VTube Studio
VTS_WS_URL = "ws://localhost:8001"
PLUGIN_NAME = "VTS_Enhanced_MVP"
PLUGIN_DEVELOPER = "LocalUser"

# Hotkey mappings
EMO_TO_HOTKEY = {
    "neutral": "emo_neutral",
    "happy": "emo_happy",
    "angry": "emo_angry",
    "sad": "emo_sad",
    "surprised": "emo_surprised",
}
POSE_TO_HOTKEY = {
    "idle": "pose_idle",
    "talk": "pose_talk",
    "think": "pose_think",
}

# VAD / Audio
SAMPLE_RATE = 16000
FRAME_MS = 20
VAD_MODE = 2  # 0-3 (aggressiveness)
START_TRIGGER_FRAMES = 5  # consecutive speech frames to start
END_TRIGGER_FRAMES = 25  # consecutive non-speech frames to end
MAX_UTTERANCE_SEC = 12
MIC_DEVICE = None  # None = default
COOLDOWN_AFTER_PLAY_SEC = 0.8

# STT
WHISPER_MODEL = "small"
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE_TYPE = "float16"

# LLM
LLM_BACKEND = "ollama"  # "ollama" | "mock" | "openai_compat"
TEMPERATURE = 0.4

# Ollama
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b-instruct"
OLLAMA_TIMEOUT_SEC = 30

# TTS
TTS_VOICE = "zh-CN-XiaoxiaoNeural"
TTS_FORMAT = "riff-16khz-16bit-mono-pcm"
