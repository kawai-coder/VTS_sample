# VTS Enhanced MVP

Python 3.10+ 的本地链路示例：持续监听麦克风 → VAD 自动断句 → faster-whisper 转写 → Ollama 本地 LLM 生成 JSON 回复 → edge-tts 生成语音并播放 → 触发 VTube Studio Hotkey。

## 功能概览
- 持续监听 + webrtcvad 自动断句
- faster-whisper 准流式转写
- LLM 默认 Ollama（本地）
- TTS 使用 edge-tts，播放期间暂停麦克风
- VTube Studio WebSocket API：认证、拉取 hotkey、触发 hotkey

## 前置准备
### 1) VTube Studio Plugin API
1. 打开 VTube Studio → Settings → Plugin API → Enable。
2. 运行本项目后，会弹出授权请求，确认即可生成 token。

### 2) 创建 Hotkey
在 VTube Studio 中创建以下 Hotkey（名称需一致）：
- emo_happy / emo_angry / emo_sad / emo_surprised / emo_neutral
- pose_talk / pose_idle / pose_think

### 3) 安装依赖
```bash
pip install -r requirements.txt
```

### 4) Ollama
1. 安装 Ollama 并确保 `ollama serve` 正在运行。
2. 拉取模型：
```bash
ollama pull <model>
```
3. 确认接口可用：访问 `http://localhost:11434`。
4. 在 `config.py` 中设置 `OLLAMA_MODEL` 为拉取的模型名称。

## 运行
```bash
python main.py
```

列出输入设备：
```bash
python main.py --list-devices
```

调试模式（保存 wav / STT / LLM JSON 到 runs/）：
```bash
python main.py --debug
```

## 常见问题
- **找不到麦克风设备**：运行 `python main.py --list-devices` 查看设备索引，并在 `config.py` 中设置 `MIC_DEVICE`。
- **VTS 连接失败**：确认 VTube Studio 的 Plugin API 已开启，地址为 `ws://localhost:8001`。
- **Ollama 连接失败**：确认 `ollama serve` 正在运行，`OLLAMA_HOST` 配置正确。
- **STT 模型缺失**：首次运行会下载 whisper 模型，或手动设置 `WHISPER_MODEL`。

## 口型同步建议
建议使用虚拟声卡把 TTS 音频送入 VTube Studio 的 LipSync 输入（本项目不做虚拟声卡配置）。
