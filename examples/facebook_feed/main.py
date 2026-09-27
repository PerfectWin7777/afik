"""
PyFlutter Example: Social Feed (Facebook style).
Demonstrates Pythonic, Object-Oriented component architecture:
- Domain data modeling with @dataclass
- Reusable UI components (inheriting from Component / StatelessWidget)
- Fluent widget modifiers (.padding(), .card(), .center())
- Typed constants for Icons and Colors
"""

from __future__ import annotations

from dataclasses import dataclass
from pyflutter import (
    AppBar,
    BottomNavigationBar,
    BottomNavigationBarItem,
    Card,
    Colors,
    Column,
    Component,
    Container,
    Divider,
    Icon,
    Icons,
    Image,
    ListView,
    Row,
    Scaffold,
    SizedBox,
    Text,
    run,
)
from pyflutter.core.logger import logger


@dataclass
class Post:
    """Domain model representing a social media publication."""
    id: str
    author: str
    time_ago: str
    avatar_url: str
    text: str
    image_url: str
    likes_count: int = 0
    comments_count: int = 14
    shares_count: int = 5
    is_liked: bool = False


class ActionButton(Component):
    """Reusable post action button (Like, Comment, Share)."""

    def __init__(
        self,
        icon: str,
        label: str,
        *,
        on_click=None,
        active: bool = False,
        active_color: str = Colors.BLUE,
    ):
        super().__init__()
        self.icon = icon
        self.label = label
        self.on_click = on_click
        self.active = active
        self.active_color = active_color

    def build(self):
        color = self.active_color if self.active else Colors.GREY
        return Container(
            Row([
                Icon(self.icon, size=18, color=color),
                SizedBox(width=6),
                Text(self.label, font_size=13, font_weight="bold", color=color),
            ], main_axis_alignment="center"),
            padding=6,
            on_click=self.on_click,
        )


class PostHeader(Component):
    """Encapsulates the author avatar, name, timestamp, and menu icon."""

    def __init__(self, post: Post):
        super().__init__()
        self.post = post

    def build(self):
        return Row([
            # Avatar
            Image(
                self.post.avatar_url,
                width=44,
                height=44,
                border_radius=22,
                fit="cover",
            ),
            SizedBox(width=12),
            # Author & Time
            Column([
                Text(self.post.author, font_size=15, font_weight="bold", color="#1C1E21"),
                SizedBox(height=2),
                Row([
                    Text(self.post.time_ago, font_size=12, color=Colors.GREY),
                    SizedBox(width=4),
                    Icon(Icons.PUBLIC, size=13, color=Colors.GREY),
                ]),
            ]),
            # Trailing icon
            Icon(Icons.MORE_HORIZ, size=20, color=Colors.GREY),
        ], main_axis_alignment="space_between")


class PostCard(Component):
    """Full social post card component."""

    def __init__(self, post: Post, on_like_toggle=None):
        super().__init__()
        self.post = post
        self.on_like_toggle = on_like_toggle

    def build(self):
        like_icon = Icons.THUMB_UP if self.post.is_liked else Icons.THUMB_UP_OUTLINED
        like_count = f"👍 {self.post.likes_count} J'aime"

        stats_row = Row([
            Text(like_count, font_size=12, color=Colors.GREY),
            Text(
                f"{self.post.comments_count} commentaires · {self.post.shares_count} partages",
                font_size=12,
                color=Colors.GREY,
            ),
        ], main_axis_alignment="space_between").padding(vertical=6)

        actions_row = Row([
            ActionButton(
                icon=like_icon,
                label="J'aime",
                on_click=self.on_like_toggle,
                active=self.post.is_liked,
            ),
            ActionButton(
                icon=Icons.COMMENT,
                label="Commenter",
            ),
            ActionButton(
                icon=Icons.SHARE,
                label="Partager",
            ),
        ], main_axis_alignment="space_between")

        return Card(
            Column([
                PostHeader(self.post),
                Text(self.post.text, font_size=14, color="#050505").padding(vertical=8),
                Image(self.post.image_url, height=220, fit="cover"),
                stats_row,
                Divider(height=1),
                actions_row,
            ]),
            padding=12,
            elevation=2,
            margin=8,
            border_radius=12,
        )


class SocialFeedApp(Component):
    """Main Application component."""

    def __init__(self):
        super().__init__()
        self.current_tab = 0
        self.posts = [
            Post(
                id="post-1",
                author="Tony Dev",
                time_ago="À l'instant",
                avatar_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100",
                text="🚀 PyFlutter avec une vraie architecture POO Pythonique !\nComposants réutilisables, Dataclasses, modificateurs et typage complet.",
                image_url="https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600",
                likes_count=42,
            ),
            Post(
                id="post-2",
                author="Google Flutter Team",
                time_ago="Il y a 3 heures",
                avatar_url="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100",
                text="Les icônes Material et les thèmes de couleurs sont maintenant accessibles avec auto-complétion complète dans l'IDE !",
                image_url="https://images.unsplash.com/photo-1518770660439-4636190af475?w=600",
                likes_count=128,
            ),
        ]

    def toggle_like(self, post: Post):
        post.is_liked = not post.is_liked
        post.likes_count += 1 if post.is_liked else -1
        logger.info(f"Post {post.id} like toggled: is_liked={post.is_liked}, count={post.likes_count}")

    def on_tab_selected(self, idx: int):
        self.current_tab = idx
        logger.info(f"Tab switched to: {idx}")

    def build(self):
        post_widgets = [
            PostCard(
                post=p,
                on_like_toggle=(lambda target=p: self.toggle_like(target)) if p.id == "post-1" else None,
            )
            for p in self.posts
        ]

        app_bar = AppBar(
            title=Text("PyFlutter", font_size=20, font_weight="bold", color=Colors.WHITE),
            background_color=Colors.BLUE,
            elevation=1,
            actions=[
                Container(Icon(Icons.SEARCH, color=Colors.WHITE, size=22), padding=8),
                Container(Icon(Icons.CHAT, color=Colors.WHITE, size=22), padding=8),
            ],
        )

        nav_bar = BottomNavigationBar(
            items=[
                BottomNavigationBarItem(Icons.HOME, "Accueil"),
                BottomNavigationBarItem(Icons.VIDEO_LIBRARY, "Vidéos"),
                BottomNavigationBarItem(Icons.NOTIFICATIONS, "Alertes"),
                BottomNavigationBarItem(Icons.MENU, "Menu"),
            ],
            current_index=self.current_tab,
            selected_color=Colors.BLUE,
            unselected_color=Colors.GREY,
            on_tap=self.on_tab_selected,
        )

        return Scaffold(
            app_bar=app_bar,
            body=ListView(post_widgets, padding=8),
            bottom_navigation_bar=nav_bar,
            background_color=Colors.LIGHT_GREY,
        )


if __name__ == "__main__":
    run(SocialFeedApp())
