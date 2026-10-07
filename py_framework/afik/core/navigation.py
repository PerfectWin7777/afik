"""
Afik Multi-Page Navigator and Routing System.
Provides native-identical imperative (push/pop) and declarative (named routes)
page stack management with automatic AppBar back button synthesis.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from afik.core.logger import logger


class _NavigatorState:
    """
    Singleton holding the active page stack and registered route registry.
    """

    def __init__(self):
        self._stack: list[Any] = []
        self._routes: dict[str, Callable[..., Any]] = {}
        self._history: list[str] = []

    def set_routes(self, routes: dict[str, Callable[..., Any]]) -> None:
        self._routes = dict(routes)

    def set_initial_page(self, page: Any) -> None:
        if not self._stack:
            self._stack.append(page)
        else:
            # Rebuilding root screen: update root slot in stack to stay reactive
            self._stack[0] = page

    def push(self, page: Any) -> None:
        """
        Pushes a new page widget onto the navigation stack.
        Automatically triggers an immediate UI re-render.
        """
        self._stack.append(page)
        logger.debug(f"[Navigator] push -> stack depth: {len(self._stack)} ({page.__class__.__name__})")
        from afik.app import update
        update()

    def pop(self) -> Optional[Any]:
        """
        Pops the current top page from the stack.
        Automatically triggers an immediate UI re-render.
        """
        if len(self._stack) > 1:
            popped = self._stack.pop()
            logger.debug(f"[Navigator] pop -> stack depth: {len(self._stack)} (popped {popped.__class__.__name__})")
            from afik.app import update
            update()
            return popped
        logger.warning("[Navigator] pop ignored: stack has only 1 page (cannot pop root).")
        return None

    def push_replacement(self, page: Any) -> None:
        """
        Replaces the top-most page on the stack with a new page.
        """
        if self._stack:
            self._stack.pop()
        self.push(page)

    def push_named(self, route_name: str, arguments: Optional[dict[str, Any]] = None) -> None:
        """
        Pushes a named route defined in MaterialApp(routes={...}).
        """
        if route_name not in self._routes:
            raise KeyError(f"Route '{route_name}' is not registered in MaterialApp(routes=...).")

        builder = self._routes[route_name]
        page = builder(arguments) if arguments is not None else builder()
        self.push(page)

    def can_pop(self) -> bool:
        """Returns True if there is at least one sub-page that can be popped."""
        return len(self._stack) > 1

    def current_page(self) -> Optional[Any]:
        """Returns the page currently at the top of the stack."""
        return self._stack[-1] if self._stack else None

    def reset(self, root_page: Optional[Any] = None) -> None:
        """Clears the stack and optionally sets a new root."""
        self._stack.clear()
        if root_page is not None:
            self._stack.append(root_page)


# Global Navigator singleton
Navigator = _NavigatorState()
