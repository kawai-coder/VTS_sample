import json
import re
from typing import Any, Optional

import requests

from config import (
    LLM_BACKEND,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SEC,
    TEMPERATURE,
)

JSON_SCHEMA_REMINDER = (
    "You must output ONLY valid JSON with keys: reply, emo, pose. "
    "emo must be {label: one of neutral|happy|angry|sad|surprised, intensity: 0~1}. "
    "pose must be one of idle|talk|think. No extra text."
)


class LLMDriver:
    def __init__(self) -> None:
        self.backend = LLM_BACKEND
        if self.backend == "ollama":
            if not self._check_ollama():
                print("[LLM] Ollama unavailable, switching to mock")
                self.backend = "mock"
        print(f"[LLM] Backend: {self.backend}")

    def _check_ollama(self) -> bool:
        try:
            resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            ok = resp.status_code == 200
            print(f"[LLM] Ollama health: {resp.status_code}")
            return ok
        except requests.RequestException as exc:
            print(f"[LLM] Ollama health check failed: {exc}")
            return False

    def generate(self, user_text: str) -> dict[str, Any]:
        if self.backend == "ollama":
            return self._ollama_chat(user_text)
        if self.backend == "openai_compat":
            return self._openai_compat_stub(user_text)
        return self._mock_llm(user_text)

    def _ollama_chat(self, user_text: str) -> dict[str, Any]:
        system_prompt = (
            "You are a VTuber assistant. Reply in Chinese. "
            + JSON_SCHEMA_REMINDER
        )
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            "stream": False,
            "options": {"temperature": TEMPERATURE},
        }
        try:
            resp = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json=payload,
                timeout=OLLAMA_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            content = resp.json().get("message", {}).get("content", "")
            return self._ensure_json(content, user_text)
        except requests.RequestException as exc:
            print(f"[LLM] Ollama request failed: {exc}")
            return self._mock_llm(user_text)

    def _openai_compat_stub(self, user_text: str) -> dict[str, Any]:
        print("[LLM] OpenAI-compatible backend not implemented, using mock")
        return self._mock_llm(user_text)

    def _mock_llm(self, user_text: str) -> dict[str, Any]:
        return {
            "reply": f"(mock) 收到：{user_text}",
            "emo": {"label": "neutral", "intensity": 0.3},
            "pose": "talk",
        }

    def _ensure_json(self, content: str, fallback_text: str) -> dict[str, Any]:
        parsed = self._parse_json(content)
        if parsed is not None:
            print(f"[LLM] JSON: {parsed}")
            return parsed

        repair_prompt = (
            "Convert the following to strict JSON only. "
            + JSON_SCHEMA_REMINDER
            + "\nTEXT:\n"
            + content
        )
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": JSON_SCHEMA_REMINDER},
                {"role": "user", "content": repair_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0},
        }
        try:
            resp = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json=payload,
                timeout=OLLAMA_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            fixed = resp.json().get("message", {}).get("content", "")
            parsed = self._parse_json(fixed)
            if parsed is not None:
                print(f"[LLM] Repaired JSON: {parsed}")
                return parsed
        except requests.RequestException as exc:
            print(f"[LLM] Repair request failed: {exc}")

        return {
            "reply": fallback_text[:200],
            "emo": {"label": "neutral", "intensity": 0.3},
            "pose": "talk",
        }

    def _parse_json(self, content: str) -> Optional[dict[str, Any]]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
