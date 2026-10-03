"""
PyFlutter / Flarix Example: Social Feed (Facebook style).
Demonstrates Pythonic, Object-Oriented component architecture:
- Domain data modeling with @dataclass
- Reusable UI components (inheriting from Component)
- Fluent widget modifiers (.padding(), .card(), .center())
- Typed constants for Icons and Colors
- Reactive state management with self.update()
- Native overlay integrations (SnackBar, Share sheet)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# Auto-detect framework root so script can run seamlessly from any interpreter or directory
_repo_root = Path(__file__).resolve().parents[2]
_framework_path = _repo_root / "py_framework"
if _framework_path.exists() and str(_framework_path) not in sys.path:
    sys.path.insert(0, str(_framework_path))

from pyflutter import (
    AppBar,
    BottomNavigationBar,
    BottomNavigationBarItem,
    BoxFit,
    Card,
    Center,
    Colors,
    Column,
    Component,
    Container,
    Divider,
    ElevatedButton,
    FontWeight,
    Icon,
    Icons,
    Image,
    ListView,
    MainAxisAlignment,
    OutlinedButton,
    Row,
    Scaffold,
    SizedBox,
    Text,
    TextButton,
    TextField,
    run,
    show_snack_bar,
)
from pyflutter.core.logger import logger
from pyflutter.plugins import share_plus


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
                Text(self.label, font_size=13, font_weight=FontWeight.BOLD, color=color),
            ], main_axis_alignment=MainAxisAlignment.CENTER),
            padding=8,
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
                fit=BoxFit.COVER,
            ),
            SizedBox(width=12),
            # Author & Time
            Column([
                Text(self.post.author, font_size=15, font_weight=FontWeight.BOLD, color=Colors.DARK_GREY),
                SizedBox(height=2),
                Row([
                    Text(self.post.time_ago, font_size=12, color=Colors.GREY),
                    SizedBox(width=4),
                    Icon(Icons.PUBLIC, size=13, color=Colors.GREY),
                ]),
            ]),
            # Trailing icon
            Icon(Icons.MORE_HORIZ, size=20, color=Colors.GREY),
        ], main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN)


class PostCard(Component):
    """Full social post card component."""

    def __init__(self, post: Post, on_like_toggle=None, on_comment=None, on_share=None):
        super().__init__()
        self.post = post
        self.on_like_toggle = on_like_toggle
        self.on_comment = on_comment
        self.on_share = on_share

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
        ], main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN).padding(vertical=6)

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
                on_click=self.on_comment,
            ),
            ActionButton(
                icon=Icons.SHARE,
                label="Partager",
                on_click=self.on_share,
            ),
        ], main_axis_alignment=MainAxisAlignment.SPACE_BETWEEN)

        return Card(
            Column([
                PostHeader(self.post),
                Text(self.post.text, font_size=14, color=Colors.TEXT_PRIMARY).padding(vertical=8),
                Image(self.post.image_url, height=220, fit=BoxFit.COVER),
                stats_row,
                Divider(height=1),
                actions_row,
            ]),
            padding=12,
            elevation=2,
            margin=8,
            border_radius=12,
        )


class CreatePostBox(Component):
    """Interactive status publisher card at the top of the feed."""

    def __init__(self, on_create_post=None):
        super().__init__()
        self.on_create_post = on_create_post

    def build(self):
        return Card(
            Column([
                Row([
                    Image(
                        "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100",
                        width=40,
                        height=40,
                        border_radius=20,
                        fit=BoxFit.COVER,
                    ),
                    SizedBox(width=10),
                    Container(
                        Text("Quoi de neuf, Tony ?", font_size=14, color=Colors.GREY),
                        padding=10,
                        border_radius=20,
                        color=Colors.INPUT_BACKGROUND,
                        on_click=self.on_create_post,
                    ),
                ]),
                Divider(height=1).padding(vertical=8),
                Row([
                    TextButton(
                        text="Direct",
                        icon=Icons.VIDEOCAM,
                        color=Colors.RED,
                    ),
                    TextButton(
                        text="Photo",
                        icon=Icons.PHOTO_LIBRARY,
                        color=Colors.GREEN_ACCENT,
                        on_click=self.on_create_post,
                    ),
                    TextButton(
                        text="Humeur",
                        icon=Icons.MOOD,
                        color=Colors.AMBER_ACCENT,
                    ),
                ], main_axis_alignment=MainAxisAlignment.SPACE_AROUND),
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
                text="🚀 Flarix avec une vraie architecture POO Pythonique !\nComposants réutilisables, Dataclasses, modificateurs et typage complet.",
                image_url="https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600",
                likes_count=42,
                comments_count=14,
                shares_count=5,
            ),
            Post(
                id="post-2",
                author="Google Flutter Team",
                time_ago="Il y a 3 heures",
                avatar_url="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100",
                text="Les icônes Material et les thèmes de couleurs sont maintenant accessibles avec auto-complétion complète dans l'IDE !",
                image_url="https://images.unsplash.com/photo-1518770660439-4636190af475?w=600",
                likes_count=128,
                comments_count=32,
                shares_count=18,
            ),
        ]

    def toggle_like(self, post: Post):
        post.is_liked = not post.is_liked
        post.likes_count += 1 if post.is_liked else -1
        logger.info(f"Post {post.id} like toggled: is_liked={post.is_liked}, count={post.likes_count}")
        self.update()

    def comment_post(self, post: Post):
        post.comments_count += 1
        show_snack_bar(f"Commentaire ajouté au post de {post.author} !")
        self.update()

    def share_post(self, post: Post):
        post.shares_count += 1
        share_plus.share(text=f"{post.author}: {post.text}")
        show_snack_bar(f"Publication de {post.author} partagée !")
        self.update()

    def add_new_post(self):
        new_post = Post(
            id=f"post-{len(self.posts) + 1}",
            author="Tony Dev",
            time_ago="À l'instant",
            avatar_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100",
            text="✨ Nouvelle publication créée en direct via Flarix !",
            image_url="https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600",
            likes_count=0,
            comments_count=0,
            shares_count=0,
        )
        self.posts.insert(0, new_post)
        show_snack_bar("🎉 Nouvelle publication ajoutée au fil !")
        self.update()

    def on_tab_selected(self, idx: int):
        self.current_tab = idx
        logger.info(f"Tab switched to: {idx}")
        self.update()

    def build(self):
        post_widgets = [
            CreatePostBox(on_create_post=self.add_new_post),
            *[
                PostCard(
                    post=p,
                    on_like_toggle=lambda target=p: self.toggle_like(target),
                    on_comment=lambda target=p: self.comment_post(target),
                    on_share=lambda target=p: self.share_post(target),
                )
                for p in self.posts
            ]
        ]

        app_bar = AppBar(
            title=Text("Flarix Social", font_size=20, font_weight=FontWeight.BOLD, color=Colors.WHITE),
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
            background_color=Colors.BACKGROUND,
        )


# Backward compatibility alias
App = SocialFeedApp

if __name__ == "__main__":
    run(SocialFeedApp())
