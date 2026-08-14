"""Network logger module for recording Chrome HTTP traffic."""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class NetworkLogger:
    """Captures network requests and console messages from a Playwright BrowserContext."""

    def __init__(self):
        self.network_logs: List[Dict[str, Any]] = []
        self.console_logs: List[str] = []
        self._pending_requests: Dict[int, Dict[str, Any]] = {}

    def attach_to_context(self, context):
        """Attach listeners to a Playwright context."""
        context.on("request", self._on_request)
        context.on("response", self._on_response)
        context.on("requestfailed", self._on_request_failed)

    def attach_to_page(self, page):
        """Attach console listener to a Playwright page."""
        page.on("console", self._on_console)

    def _on_request(self, request):
        post_data = None
        try:
            post_data = request.post_data
        except Exception:
            try:
                raw_buf = request.post_data_buffer
                if raw_buf:
                    post_data = f"<binary {len(raw_buf)} bytes>"
            except Exception:
                post_data = None

        req_info = {
            "id": id(request),
            "timestamp": datetime.now().isoformat(),
            "url": request.url,
            "method": request.method,
            "resource_type": request.resource_type,
            "headers": dict(request.headers),
            "post_data": post_data,
            "status": None,
            "response_headers": None,
            "error": None
        }
        self._pending_requests[id(request)] = req_info

    async def _on_response(self, response):
        req_id = id(response.request)
        req_info = self._pending_requests.get(req_id)
        if req_info:
            req_info["status"] = response.status
            req_info["response_headers"] = dict(response.headers)
            
            content_type = response.headers.get("content-type", "")
            if "json" in content_type or "text" in content_type or "api" in response.url:
                try:
                    text_body = await response.text()
                    if len(text_body) > 2000:
                        req_info["response_body_snippet"] = text_body[:2000] + " ...[truncated]"
                    else:
                        req_info["response_body_snippet"] = text_body
                except Exception as e:
                    req_info["response_body_error"] = str(e)

            self.network_logs.append(req_info)

    def _on_request_failed(self, request):
        req_id = id(request)
        req_info = self._pending_requests.get(req_id)
        if req_info:
            req_info["error"] = str(request.failure)
            self.network_logs.append(req_info)

    def _on_console(self, msg):
        self.console_logs.append(f"[{msg.type}] {msg.text}")

    def export_json(self, output_path: str) -> str:
        """Export captured network logs and console messages to a JSON file."""
        data = {
            "summary": {
                "total_requests": len(self.network_logs),
                "total_console_logs": len(self.console_logs),
                "exported_at": datetime.now().isoformat()
            },
            "console_logs": self.console_logs,
            "network_requests": self.network_logs
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return output_path
