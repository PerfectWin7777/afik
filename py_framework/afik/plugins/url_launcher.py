"""
Afik url_launcher plugin wrapper.
Provides Pythonic APIs to launch URLs, phone dialer, and email clients
using Flutter's official url_launcher package.
"""

from __future__ import annotations

from afik.plugins.manager import invoke_plugin_method


def open_url(url: str) -> None:
    """
    Opens the specified web URL in the device's default browser or external application.
    Example:
        url_launcher.open_url("https://fakestoreapi.com")
    """
    invoke_plugin_method("url_launcher", "open_url", {"url": str(url)})


def make_call(phone_number: str) -> None:
    """
    Opens the device's phone dialer with the specified number.
    Example:
        url_launcher.make_call("+33123456789")
    """
    invoke_plugin_method("url_launcher", "make_call", {"phone": str(phone_number)})


def send_email(email_address: str, subject: str = "") -> None:
    """
    Opens the device's default email client.
    Example:
        url_launcher.send_email("support@pyshop.com", subject="Question")
    """
    invoke_plugin_method("url_launcher", "send_email", {"email": str(email_address), "subject": str(subject)})
