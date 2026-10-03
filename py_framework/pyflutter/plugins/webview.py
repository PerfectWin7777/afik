"""
PyFlutter WebView plugin (webview_flutter).
Provides in-app web browsing controllers and JavaScript evaluation.
"""

from __future__ import annotations

import itertools
from typing import Any, Optional
from pyflutter.plugins.manager import call_plugin


_webview_counter = itertools.count()


class WebViewController:
    """Controls an embedded web view instance."""

    def __init__(self, initial_url: str = "about:blank", view_id: Optional[str] = None):
        self.view_id = view_id or f"web_{next(_webview_counter)}"
        self._current_url = initial_url
        if initial_url != "about:blank":
            self.load_url(initial_url)

    def load_url(self, url: str) -> bool:
        """Loads a web page from a URL."""
        self._current_url = str(url)
        call_plugin("webview", "loadUrl", {"viewId": self.view_id, "url": str(url)})
        return True

    def load_html(self, html: str) -> bool:
        """Loads raw HTML string."""
        self._current_url = "data:text/html;charset=utf-8,..."
        call_plugin("webview", "loadHtml", {"viewId": self.view_id, "html": str(html)})
        return True

    def reload(self) -> bool:
        """Reloads the current page."""
        call_plugin("webview", "reload", {"viewId": self.view_id})
        return True

    def go_back(self) -> bool:
        """Navigates back in browsing history."""
        res = call_plugin("webview", "goBack", {"viewId": self.view_id})
        return bool(isinstance(res, dict) and res.get("success", False))

    def go_forward(self) -> bool:
        """Navigates forward in browsing history."""
        res = call_plugin("webview", "goForward", {"viewId": self.view_id})
        return bool(isinstance(res, dict) and res.get("success", False))

    def can_go_back(self) -> bool:
        """Checks if there is history to navigate back."""
        res = call_plugin("webview", "canGoBack", {"viewId": self.view_id})
        return bool(isinstance(res, dict) and res.get("canGoBack", False))

    def can_go_forward(self) -> bool:
        """Checks if there is history to navigate forward."""
        res = call_plugin("webview", "canGoForward", {"viewId": self.view_id})
        return bool(isinstance(res, dict) and res.get("canGoForward", False))

    def evaluate_javascript(self, script: str) -> Any:
        """Evaluates JavaScript code and returns the result."""
        res = call_plugin("webview", "evaluateJavascript", {"viewId": self.view_id, "script": str(script)})
        if isinstance(res, dict) and "result" in res:
            return res["result"]
        return res

    def current_url(self) -> str:
        """Returns the current loaded URL."""
        res = call_plugin("webview", "currentUrl", {"viewId": self.view_id})
        if isinstance(res, dict) and "url" in res:
            self._current_url = str(res["url"])
        return self._current_url


from pyflutter.widgets.widgets import WebView

__all__ = [
    "WebViewController",
    "WebView",
]

