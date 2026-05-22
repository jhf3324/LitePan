"""STRM 播放链接签名工具。"""

import base64
import hashlib
import hmac
import urllib.parse

from config import Settings


def build_strm_play_path(account_id: int, file_id: str) -> str:
    encoded_file_id = urllib.parse.quote(str(file_id).lstrip("/"), safe="/")
    return f"/api/strm/play/{int(account_id)}/{encoded_file_id}"


def sign_strm_path(path: str) -> str:
    secret = str(Settings.SECRET_KEY or "litepan-strm").encode("utf-8")
    digest = hmac.new(secret, str(path).encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def verify_strm_signature(path: str, signature: str) -> bool:
    expected = sign_strm_path(path)
    return hmac.compare_digest(expected, str(signature or "").strip())
