from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Xóa context cũ để request này không bị dính dữ liệu request trước
        clear_contextvars()

        # 2. Nếu client gửi x-request-id thì dùng lại
        # Nếu không có thì tự tạo dạng req-xxxxxxxx
        incoming_id = request.headers.get("x-request-id")
        correlation_id = incoming_id or f"req-{uuid.uuid4().hex[:8]}"

        # 3. Gắn correlation_id vào structlog
        # Từ đây mọi log trong request này sẽ có correlation_id
        bind_contextvars(correlation_id=correlation_id)

        # 4. Lưu correlation_id vào request.state để lát nữa trả về response
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response = await call_next(request)
        response_time_ms = int((time.perf_counter() - start) * 1000)

        # 5. Trả correlation_id và thời gian xử lý ra header
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(response_time_ms)

        return response