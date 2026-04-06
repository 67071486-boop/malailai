"""素材管理 API 封装：临时素材上传/获取、图片上传。

- 上传临时素材：`upload_temp_media`
- 上传图片（返回永久 URL）：`upload_image`
- 获取临时素材：`get_temp_media`

说明：
- 企业微信要求 multipart/form-data，字段名固定为 `media`（上传临时素材）。
- `upload_image` 可使用任意字段名，默认也使用 `media` 以保持一致。
- get 接口可能返回二进制流或 JSON 错误体，调用方需根据 `Content-Type` 处理。
"""
from typing import Dict, Optional
import os
import mimetypes
import requests
from tenacity import retry, stop_after_attempt, wait_exponential  # type: ignore

from .base import BaseClient, WeComApiError

_ALLOWED_MEDIA_TYPES = {"image", "voice", "video", "file"}


def _guess_mime(path: str, fallback: str = "application/octet-stream") -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or fallback


class MediaApi(BaseClient):
    def upload_temp_media(
        self,
        access_token: str,
        media_type: str,
        file_path: str,
        *,
        field_name: str = "media",
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Dict:
        """上传临时素材，返回包含 `media_id`、`type`、`created_at`。

        `media_type` 必须是 image|voice|video|file；文件大小需满足企业微信限制。
        """
        if media_type not in _ALLOWED_MEDIA_TYPES:
            raise WeComApiError(f"invalid media_type: {media_type}")
        if not os.path.isfile(file_path):
            raise WeComApiError(f"file not found: {file_path}")
        if not access_token:
            raise WeComApiError("missing access_token")

        url = (
            "https://qyapi.weixin.qq.com/cgi-bin/media/upload"
            f"?access_token={access_token}&type={media_type}"
        )
        fname = filename or os.path.basename(file_path)
        ctype = content_type or _guess_mime(file_path)

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5), reraise=True)
        def _call():
            with open(file_path, "rb") as f:
                files = {field_name: (fname, f, ctype)}
                resp = self.session.post(url, files=files, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()

        try:
            data = _call()
        except requests.RequestException as exc:
            raise WeComApiError(f"HTTP upload failed for {url}: {exc}")
        except ValueError as exc:
            raise WeComApiError(f"Invalid JSON response for upload_temp_media: {exc}")

        self._raise_if_errcode(data, "upload_temp_media", required_keys=["media_id"])
        return data

    def upload_image(
        self,
        access_token: str,
        file_path: str,
        *,
        field_name: str = "media",
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Dict:
        """上传图片，返回永久有效的 `url`。仅用于图文消息/欢迎语展示。"""
        if not os.path.isfile(file_path):
            raise WeComApiError(f"file not found: {file_path}")
        if not access_token:
            raise WeComApiError("missing access_token")

        url = "https://qyapi.weixin.qq.com/cgi-bin/media/uploadimg"
        fname = filename or os.path.basename(file_path)
        ctype = content_type or _guess_mime(file_path, "image/png")

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5), reraise=True)
        def _call():
            with open(file_path, "rb") as f:
                files = {field_name: (fname, f, ctype)}
                resp = self.session.post(url, params={"access_token": access_token}, files=files, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()

        try:
            data = _call()
        except requests.RequestException as exc:
            raise WeComApiError(f"HTTP uploadimg failed for {url}: {exc}")
        except ValueError as exc:
            raise WeComApiError(f"Invalid JSON response for upload_image: {exc}")

        self._raise_if_errcode(data, "upload_image", required_keys=["url"])
        return data

    def get_temp_media(
        self,
        access_token: str,
        media_id: str,
        *,
        range_header: Optional[str] = None,
        stream: bool = True,
    ) -> requests.Response:
        """获取临时素材。

        - 对于大文件可传入 `range_header`（例如 "bytes=0-1023"）以分块下载。
        - 返回 `requests.Response`，调用方需检查 `Content-Type` 是否为 JSON 错误体。
        """
        if not access_token:
            raise WeComApiError("missing access_token")
        if not media_id:
            raise WeComApiError("missing media_id")

        url = "https://qyapi.weixin.qq.com/cgi-bin/media/get"
        headers = {"Range": range_header} if range_header else None

        try:
            resp = self.session.get(
                url,
                params={"access_token": access_token, "media_id": media_id},
                headers=headers,
                timeout=self.timeout,
                stream=stream,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise WeComApiError(f"HTTP get_temp_media failed for {url}: {exc}")

        # 若 Content-Type 是 JSON，企业微信会返回错误体，尝试解析并抛出。
        ctype = resp.headers.get("Content-Type", "")
        if ctype.startswith("application/json"):
            try:
                data = resp.json()
            except ValueError:
                raise WeComApiError("Failed to parse JSON error body for get_temp_media")
            self._raise_if_errcode(data, "get_temp_media")
        return resp


def upload_temp_media(
    access_token: str,
    media_type: str,
    file_path: str,
    *,
    field_name: str = "media",
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    session=None,
    timeout: int = 10,
) -> Dict:
    client = MediaApi(session=session, timeout=timeout)
    return client.upload_temp_media(access_token, media_type, file_path, field_name=field_name, filename=filename, content_type=content_type)


def upload_image(
    access_token: str,
    file_path: str,
    *,
    field_name: str = "media",
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    session=None,
    timeout: int = 10,
) -> Dict:
    client = MediaApi(session=session, timeout=timeout)
    return client.upload_image(access_token, file_path, field_name=field_name, filename=filename, content_type=content_type)


def get_temp_media(
    access_token: str,
    media_id: str,
    *,
    range_header: Optional[str] = None,
    stream: bool = True,
    session=None,
    timeout: int = 10,
) -> requests.Response:
    client = MediaApi(session=session, timeout=timeout)
    return client.get_temp_media(access_token, media_id, range_header=range_header, stream=stream)
