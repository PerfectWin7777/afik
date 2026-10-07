"""
Afik MethodChannel & Platform Communication API.
Enables bidirectional RPC method calls and event streams between Python
and native Flutter / pub.dev platform plugins.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional


class PlatformException(Exception):
    """
    Exception raised when a native Flutter or platform channel invocation fails.
    Mirrors Flutter's `services.PlatformException`.
    """

    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        details: Any = None,
        stacktrace: Optional[str] = None,
    ):
        super().__init__(f"PlatformException({code}, {message}, {details})")
        self.code = code
        self.message = message
        self.details = details
        self.stacktrace = stacktrace

    def __repr__(self) -> str:
        return f"PlatformException(code={self.code!r}, message={self.message!r}, details={self.details!r})"


class MethodCall:
    """
    Represents an incoming or outgoing method invocation on a MethodChannel.
    Mirrors Flutter's `services.MethodCall`.
    """

    def __init__(self, method: str, arguments: Any = None):
        self.method = str(method)
        self.arguments = arguments

    def __repr__(self) -> str:
        return f"MethodCall(method={self.method!r}, arguments={self.arguments!r})"


# Registry for Python-side method call handlers and mock handlers for unit tests
_channel_handlers: dict[str, Callable[[MethodCall], Any]] = {}
_mock_method_handlers: dict[str, Callable[[MethodCall], Any]] = {}
_registry_lock = threading.Lock()


def register_channel_handler(channel_name: str, handler: Optional[Callable[[MethodCall], Any]]) -> None:
    """Registers a Python handler for incoming platform method calls on a channel."""
    with _registry_lock:
        if handler is None:
            _channel_handlers.pop(channel_name, None)
        else:
            _channel_handlers[channel_name] = handler


def get_channel_handler(channel_name: str) -> Optional[Callable[[MethodCall], Any]]:
    """Retrieves the registered handler for a channel."""
    with _registry_lock:
        return _channel_handlers.get(channel_name)


def set_mock_method_call_handler(
    channel_name: str,
    handler: Optional[Callable[[MethodCall], Any]],
) -> None:
    """
    Sets a mock method call handler for testing channel calls in Python unit tests
    without requiring a live Flutter runtime.
    """
    with _registry_lock:
        if handler is None:
            _mock_method_handlers.pop(channel_name, None)
        else:
            _mock_method_handlers[channel_name] = handler


def get_mock_method_call_handler(channel_name: str) -> Optional[Callable[[MethodCall], Any]]:
    """Retrieves any active mock method handler for a channel."""
    with _registry_lock:
        return _mock_method_handlers.get(channel_name)


class MethodChannel:
    """
    A named channel for communicating with Flutter plugins and arbitrary `pub.dev` packages
    using asynchronous method calls.

    Mirrors Flutter's `MethodChannel` API:
        ```python
        import afik as pf

        channel = pf.MethodChannel("plugins.flutter.io/battery")
        battery_level = channel.invoke_method("getBatteryLevel")
        ```
    """

    def __init__(self, name: str):
        if not name or not isinstance(name, str):
            raise ValueError("MethodChannel name must be a non-empty string.")
        self.name = str(name)

    def invoke_method(
        self,
        method: str,
        arguments: Any = None,
        *,
        timeout: float = 5.0,
    ) -> Any:
        """
        Invokes the named `method` on this channel with optional `arguments`.
        Returns the result decoded from Dart / native platform, or raises `PlatformException`.
        """
        # 1. Check if a mock handler is configured for unit testing
        mock = get_mock_method_call_handler(self.name)
        if mock is not None:
            call = MethodCall(method, arguments)
            res = mock(call)
        else:
            # 2. Dispatch via plugin manager
            from afik.plugins.manager import call_plugin

            payload = {
                "channel": self.name,
                "method": method,
                "arguments": arguments,
            }
            res = call_plugin("__method_channel__", method, payload, timeout=timeout)

        # 3. Check for platform exception returned from Dart
        if isinstance(res, dict) and "platform_error" in res:
            err = res["platform_error"]
            if isinstance(err, dict):
                raise PlatformException(
                    code=str(err.get("code", "PLATFORM_ERROR")),
                    message=err.get("message"),
                    details=err.get("details"),
                )
            raise PlatformException(code="PLATFORM_ERROR", message=str(err))

        return res

    def set_method_call_handler(self, handler: Optional[Callable[[MethodCall], Any]]) -> None:
        """
        Sets the handler for incoming method calls initiated from Flutter or native platform.
        Pass `None` to unregister.
        """
        register_channel_handler(self.name, handler)

    def __repr__(self) -> str:
        return f"<MethodChannel name={self.name!r}>"


class EventChannel:
    """
    A named channel for subscribing to an asynchronous stream of events from Flutter.
    Mirrors Flutter's `EventChannel`.
    """

    def __init__(self, name: str):
        if not name or not isinstance(name, str):
            raise ValueError("EventChannel name must be a non-empty string.")
        self.name = str(name)
        self._listener: Optional[Callable[[Any], None]] = None

    def listen(
        self,
        on_data: Callable[[Any], None],
        *,
        on_error: Optional[Callable[[Any], None]] = None,
        arguments: Any = None,
    ) -> None:
        """Subscribes to the event stream."""
        self._listener = on_data
        from afik.plugins.manager import call_plugin

        call_plugin(
            "__event_channel__",
            "listen",
            {"channel": self.name, "arguments": arguments},
        )

    def cancel(self) -> None:
        """Cancels the active event stream subscription."""
        self._listener = None
        from afik.plugins.manager import call_plugin

        call_plugin("__event_channel__", "cancel", {"channel": self.name})

    def __repr__(self) -> str:
        return f"<EventChannel name={self.name!r}>"
