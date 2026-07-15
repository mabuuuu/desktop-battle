"""Desktop Battle - AI 客户端.

使用 httpx 调用 OpenAI 兼容 API，用于获取游戏策略建议。
支持异步调用，10秒超时。
"""

from __future__ import annotations

import json
from typing import Any

import httpx


class AIClient:
    """OpenAI 兼容 API 客户端.

    通过 api_key + api_url 调用 LLM，获取 JSON 格式的战术策略。
    """

    def __init__(
        self,
        api_key: str = "",
        api_url: str = "https://api.openai.com/v1/chat/completions",
        model: str = "gpt-4o-mini",
        timeout: float = 10.0,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> None:
        self._api_key: str = api_key
        self._api_url: str = api_url
        self._model: str = model
        self._timeout: float = timeout
        self._max_tokens: int = max_tokens
        self._temperature: float = temperature
        self._client: httpx.Client | None = None

    @property
    def is_configured(self) -> bool:
        """检查是否已配置 API 密钥."""
        return bool(self._api_key)

    def _get_client(self) -> httpx.Client:
        """获取或创建 httpx 客户端."""
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout)
        return self._client

    def send_strategy_request(
        self,
        system_prompt: str,
        user_message: str,
    ) -> dict[str, Any]:
        """发送策略请求并解析 JSON 响应.

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息 (战况描述)

        Returns:
            解析后的 JSON 策略数据

        Raises:
            httpx.HTTPError: HTTP 请求错误
            json.JSONDecodeError: JSON 解析失败
            ValueError: 响应格式不符合预期
        """
        if not self._api_key:
            raise ValueError("AI API key not configured")

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        client = self._get_client()
        response = client.post(self._api_url, json=payload, headers=headers)
        response.raise_for_status()

        data: dict[str, Any] = response.json()

        # 提取 content
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("No choices in API response")

        message = choices[0].get("message", {})
        content = message.get("content", "")
        if not content:
            raise ValueError("Empty content in API response")

        # 解析 JSON content
        try:
            strategy = json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 JSON 块
            import re
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                strategy = json.loads(match.group())
            else:
                raise

        if not isinstance(strategy, dict):
            raise ValueError(f"Expected JSON object, got {type(strategy)}")

        return strategy

    def close(self) -> None:
        """关闭 HTTP 客户端."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __del__(self) -> None:
        self.close()
