"""
PyFlutter WebView plugin (matches pub.dev package: webview_flutter).
Provides in-app web browsing controllers and JavaScript evaluation.
"""

from __future__ import annotations

import itertools
from typing import Any, Optional

from pyflutter.plugins.manager import call_plugin

_webview_counter = itertools.count()


class WebViewController:
    """Controls an embedded web view (webview_flutter).

    The controller works as soon as it is created, with or without a ``WebView`` widget on
    screen. Methods return what the platform answered.
    """

    def __init__(self, initial_url: str = "about:blank", view_id: Optional[str] = None):
        self.view_id = view_id or f"web_{next(_webview_counter)}"
        self._current_url = initial_url
        if initial_url != "about:blank":
            self.load_url(initial_url)

    def _call(self, method: str, extra: Optional[dict] = None, timeout: float = 10.0) -> Any:
        args = {"viewId": self.view_id}
        if extra:
            args.update(extra)
        return call_plugin("webview_flutter", method, args, timeout=timeout)

    def load_url(self, url: str) -> bool:
        """Loads a web page from a URL."""
        res = self._call("loadUrl", {"url": str(url)})
        if isinstance(res, dict) and isinstance(res.get("url"), str):
            self._current_url = res["url"]
            return True
        return False

    def load_html(self, html: str) -> bool:
        """Loads a raw HTML string."""
        res = self._call("loadHtml", {"html": str(html)})
        ok = isinstance(res, dict) and res.get("success") is True
        if ok:
            self._current_url = "about:blank"
        return ok

    def reload(self) -> bool:
        """Reloads the current page."""
        res = self._call("reload")
        return isinstance(res, dict) and res.get("reloaded") is True

    def go_back(self) -> bool:
        """Navigates back in the history; False when there is nothing to go back to."""
        res = self._call("goBack")
        return isinstance(res, dict) and res.get("success") is True

    def go_forward(self) -> bool:
        """Navigates forward in the history; False when there is nothing to go forward to."""
        res = self._call("goForward")
        return isinstance(res, dict) and res.get("success") is True

    def can_go_back(self) -> bool:
        res = self._call("canGoBack")
        return isinstance(res, dict) and res.get("canGoBack") is True

    def can_go_forward(self) -> bool:
        res = self._call("canGoForward")
        return isinstance(res, dict) and res.get("canGoForward") is True

    def evaluate_javascript(self, script: str) -> Any:
        """Runs JavaScript in the page and returns its result as text (None on no answer)."""
        res = self._call("evaluateJavascript", {"script": str(script)})
        if isinstance(res, dict) and "result" in res:
            return res["result"]
        return res

    def current_url(self) -> str:
        """The URL currently loaded, as reported by the platform."""
        res = self._call("currentUrl")
        if isinstance(res, dict) and isinstance(res.get("url"), str):
            self._current_url = res["url"]
        return self._current_url


from pyflutter.widgets.widgets import WebView  # noqa: E402  (re-export; widgets import this module)

__all__ = [
    "WebViewController",
    "WebView",
]
