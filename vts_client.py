import json
import uuid
from pathlib import Path
from typing import Any

from websocket import WebSocket

from config import PLUGIN_DEVELOPER, PLUGIN_NAME, TOKEN_PATH, VTS_WS_URL


class VTSClient:
    def __init__(self) -> None:
        self.ws: WebSocket | None = None
        self.token_path = TOKEN_PATH
        self.hotkeys: dict[str, str] = {}

    def connect(self) -> None:
        self.ws = WebSocket()
        self.ws.connect(VTS_WS_URL)
        print("[VTS] Connected")
        self.authenticate()
        self.refresh_hotkeys()

    def close(self) -> None:
        if self.ws is not None:
            self.ws.close()
            self.ws = None
            print("[VTS] Connection closed")

    def authenticate(self) -> None:
        token = self._load_token()
        if token:
            if self._send_request("AuthenticationRequest", {"pluginName": PLUGIN_NAME, "pluginDeveloper": PLUGIN_DEVELOPER, "authenticationToken": token}):
                print("[VTS] Authenticated with saved token")
                return
            print("[VTS] Saved token invalid, requesting new one")

        data = {
            "pluginName": PLUGIN_NAME,
            "pluginDeveloper": PLUGIN_DEVELOPER,
        }
        resp = self._send_request("AuthenticationTokenRequest", data)
        if resp:
            token = resp.get("data", {}).get("authenticationToken")
            if token:
                self._save_token(token)
                print("[VTS] Token saved")
                self._send_request("AuthenticationRequest", {"pluginName": PLUGIN_NAME, "pluginDeveloper": PLUGIN_DEVELOPER, "authenticationToken": token})

    def refresh_hotkeys(self) -> None:
        resp = self._send_request("HotkeysInCurrentModelRequest", {})
        if not resp:
            print("[VTS] Failed to fetch hotkeys")
            return
        self.hotkeys = {item["name"]: item["hotkeyID"] for item in resp.get("data", {}).get("availableHotkeys", [])}
        print(f"[VTS] Loaded hotkeys: {list(self.hotkeys.keys())}")

    def trigger_hotkey(self, name: str) -> None:
        hotkey_id = self.hotkeys.get(name)
        if not hotkey_id:
            print(f"[VTS] Hotkey not found: {name}")
            return
        self._send_request("HotkeyTriggerRequest", {"hotkeyID": hotkey_id})
        print(f"[VTS] Triggered hotkey: {name}")

    def _send_request(self, message_type: str, data: dict[str, Any]) -> dict[str, Any] | None:
        if self.ws is None:
            return None
        request_id = str(uuid.uuid4())
        payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": request_id,
            "messageType": message_type,
            "data": data,
        }
        try:
            self.ws.send(json.dumps(payload))
            raw = self.ws.recv()
            resp = json.loads(raw)
            if resp.get("messageType") == "APIError":
                print(f"[VTS] Error {message_type}: {resp}")
                return None
            return resp
        except Exception as exc:
            print(f"[VTS] Request failed: {exc}")
            return None

    def _load_token(self) -> str | None:
        if not self.token_path.exists():
            return None
        try:
            return json.loads(self.token_path.read_text(encoding="utf-8")).get("token")
        except json.JSONDecodeError:
            return None

    def _save_token(self, token: str) -> None:
        self.token_path.write_text(json.dumps({"token": token}, ensure_ascii=False, indent=2), encoding="utf-8")
