from __future__ import annotations

import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Any

import httpx


class WebhookError(RuntimeError):
    pass


def validate_url(platform: str, url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url.strip())
        port = parsed.port
    except ValueError as exc:
        raise WebhookError(f"Webhook URL 无效: {exc}") from exc
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment or port:
        raise WebhookError("Webhook 必须是无账号、无端口、无片段的 HTTPS URL")
    host = (parsed.hostname or "").lower()
    if platform == "feishu":
        if host not in {"open.feishu.cn", "open.larksuite.com"} or not parsed.path.startswith(
            "/open-apis/bot/v2/hook/"
        ):
            raise WebhookError("飞书地址必须是官方自定义机器人 Webhook")
    elif platform == "wecom":
        query = urllib.parse.parse_qs(parsed.query)
        if (
            host != "qyapi.weixin.qq.com"
            or parsed.path != "/cgi-bin/webhook/send"
            or not query.get("key")
        ):
            raise WebhookError("企业微信地址必须是官方群机器人 Webhook")
    else:
        raise WebhookError("不支持的 Webhook 平台")
    return url.strip()


def _feishu_sign(timestamp: str, secret: str) -> str:
    key = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(key, b"", digestmod=hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def _split_utf8(text: str, max_bytes: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        for char in line:
            if len((current + char).encode("utf-8")) > max_bytes:
                chunks.append(current)
                current = char
            else:
                current += char
    if current:
        chunks.append(current)
    return chunks or [""]


def send_report(platform: str, url: str, report: str, title: str, secret: str = "") -> list[dict[str, Any]]:
    url = validate_url(platform, url)
    max_bytes = 17800 if platform == "feishu" else 3800
    chunks = _split_utf8(report.strip(), max_bytes)
    responses = []
    for index, chunk in enumerate(chunks, 1):
        suffix = f"（{index}/{len(chunks)}）" if len(chunks) > 1 else ""
        if platform == "feishu":
            payload: dict[str, Any] = {
                "msg_type": "text",
                "content": {"text": f"{title}{suffix}\n\n{chunk}"},
            }
            if secret:
                timestamp = str(int(time.time()))
                payload.update({"timestamp": timestamp, "sign": _feishu_sign(timestamp, secret)})
        else:
            payload = {
                "msgtype": "markdown_v2",
                "markdown_v2": {"content": f"# {title}{suffix}\n\n{chunk}"},
            }
        try:
            response = httpx.post(url, json=payload, timeout=20, follow_redirects=False)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise WebhookError(f"{platform} 发送失败: {exc}") from exc
        ok = data.get("code", data.get("StatusCode")) == 0 if platform == "feishu" else data.get("errcode") == 0
        if not ok:
            raise WebhookError(f"{platform} 拒绝消息: {data}")
        responses.append(data)
    return responses


def configured_platforms(settings: dict[str, str]) -> list[tuple[str, str, str]]:
    output = []
    if settings.get("feishu_enabled") == "1" and settings.get("feishu_url"):
        output.append(("feishu", settings["feishu_url"], settings.get("feishu_secret", "")))
    if settings.get("wecom_enabled") == "1" and settings.get("wecom_url"):
        output.append(("wecom", settings["wecom_url"], ""))
    return output

