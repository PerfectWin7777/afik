"""
Afik Project Creator & Scaffolder.
Generates production-grade, zero-boilerplate Afik project templates.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

MAIN_PY_TEMPLATE = '''"""
Welcome to your new Afik application!
Powered by Flutter, Material 3, and Python.
"""

from __future__ import annotations
import afik as pf


class CounterApp(pf.Component):
    """
    Sample reactive counter demonstrating:
    - Material 3 ThemeData with dynamic ColorScheme.from_seed
    - Standardized typography scale (headlineMedium, titleMedium, bodyMedium)
    - Native floating SnackBar with customizable duration and undo action
    - Fast sub-millisecond hot-reload state updates
    """

    def __init__(self):
        super().__init__()
        self.counter = 0

    def increment(self):
        self.counter += 1
        self.update()

        # Show native floating SnackBar on milestone
        if self.counter % 5 == 0:
            self.show_snack_bar(
                f"🎉 Étape atteinte : {self.counter} clics !",
                duration=pf.Duration(seconds=3),
                action="Réinitialiser",
                on_action=self.reset,
            )

    def reset(self):
        self.counter = 0
        self.update()

    def build(self):
        return pf.MaterialApp(
            title="{project_title}",
            theme_mode="system",  # Automatically adapts to Android/iOS dark mode!
            theme=pf.ThemeData(
                use_material3=True,
                color_scheme=pf.ColorScheme.from_seed(seed_color="#1877F2"),
            ),
            dark_theme=pf.ThemeData(
                use_material3=True,
                color_scheme=pf.ColorScheme.from_seed(seed_color="#1877F2", brightness="dark"),
            ),
            home=pf.Scaffold(
                app_bar=pf.AppBar(
                    title="{project_title}",
                    center_title=True,
                ),
                body=pf.Center(
                    pf.Column(
                        [
                            pf.Icon(pf.Icons.ROCKET_LAUNCH, size=64, color=pf.Colors.BLUE),
                            pf.SizedBox(height=16),
                            pf.Text(
                                "Bienvenue sur Afik",
                                style="headlineMedium",
                            ),
                            pf.SizedBox(height=8),
                            pf.Text(
                                "Modifiez main.py et observez le rechargement à chaud instantané !",
                                style=pf.TextStyle(
                                    theme_style="bodyMedium",
                                    color=pf.Colors.GREY_600,
                                ),
                                text_align="center",
                            ),
                            pf.SizedBox(height=32),
                            pf.Card(
                                pf.Padding(
                                    pf.Column(
                                        [
                                            pf.Text("Compteur de clics", style="labelLarge"),
                                            pf.SizedBox(height=8),
                                            pf.Text(
                                                str(self.counter),
                                                style=pf.TextStyle(
                                                    font_size=42,
                                                    font_weight="bold",
                                                    color=pf.Colors.BLUE,
                                                ),
                                            ),
                                        ],
                                        cross_axis_alignment="center",
                                    ),
                                    padding=24,
                                ),
                            ),
                            pf.SizedBox(height=24),
                            pf.Row(
                                [
                                    pf.Button(
                                        "Incrémenter (+1)",
                                        icon=pf.Icons.ADD,
                                        on_pressed=self.increment,
                                    ),
                                    pf.SizedBox(width=12),
                                    pf.Button(
                                        "Page suivante",
                                        icon=pf.Icons.ARROW_FORWARD,
                                        on_pressed=self.open_detail_page,
                                    ),
                                ],
                                main_axis_alignment="center",
                            ),
                        ],
                        main_axis_alignment="center",
                        cross_axis_alignment="center",
                    )
                ),
            ),
        )

    def open_detail_page(self):
        """Pushes a new screen onto the multi-page stack with native back button."""
        self.navigator.push(DetailPage(self.counter))


class DetailPage(pf.Component):
    """
    Second screen pushed on the Navigator stack.
    Notice that the AppBar automatically generates the native back arrow!
    """

    def __init__(self, current_counter: int):
        super().__init__()
        self.current_counter = current_counter

    def build(self):
        return pf.Scaffold(
            app_bar=pf.AppBar(
                title="Détails du Compteur",
                center_title=True,
                # automatically_imply_leading=True by default!
            ),
            body=pf.Center(
                pf.Column(
                    [
                        pf.Icon(pf.Icons.INFO_OUTLINE, size=56, color=pf.Colors.BLUE),
                        pf.SizedBox(height=16),
                        pf.Text("Écran secondaire", style="headlineSmall"),
                        pf.SizedBox(height=8),
                        pf.Text(
                            f"Valeur reçue de la page précédente : {self.current_counter}",
                            style="bodyLarge",
                        ),
                        pf.SizedBox(height=24),
                        pf.Button(
                            "Retourner à l'accueil",
                            icon=pf.Icons.ARROW_BACK,
                            on_pressed=self.navigator.pop,
                        ),
                    ],
                    main_axis_alignment="center",
                    cross_axis_alignment="center",
                )
            ),
        )


if __name__ == "__main__":
    pf.run(CounterApp())
'''

AFIK_YAML_TEMPLATE = """name: {project_slug}
description: {description}
version: 0.1.0

# Afik project configuration
afik:
  entrypoint: main.py
  port: 7879

# Plugins from the catalog, installed on demand (`afik add <name>`, `afik plugin list`).
plugins:
  - url_launcher

# Device permissions automatically synced with Android / iOS
permissions:
  - internet
"""

GITIGNORE_TEMPLATE = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environments
.venv/
env/
venv/
ENV/

# Afik Cache
.afik/

# OS Specific
.DS_Store
Thumbs.db
"""

README_TEMPLATE = """# {project_title}

A modern mobile and desktop application powered by **Afik** (Python 3 + Flutter + Rust).

## 🚀 Lancer l'application

Pour démarrer votre application en mode développement avec Hot Reload :

```bash
afik run
```

### Raccourcis disponibles pendant l'exécution :
* `r` : **Hot Reload** (recharge le code Python instantanément sans redémarrer l'application)
* `R` : **Hot Restart** (redémarre complètement l'application Flutter)
* `q` : Quitter proprement
"""


def sanitize_project_name(name: str) -> str:
    """Converts user input name to standard snake_case slug."""
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[-\s]+", "_", slug).strip("_")
    return slug or "afik_app"


def create_project(
    project_dir: Path,
    name: str | None = None,
    description: str = "A modern mobile application powered by Afik",
) -> Path:
    """
    Creates the entire directory structure and template files for a new Afik app.
    """
    project_dir.mkdir(parents=True, exist_ok=True)

    slug = sanitize_project_name(name or project_dir.name)
    title = slug.replace("_", " ").title()

    # 1. afik.yaml
    yaml_file = project_dir / "afik.yaml"
    if not yaml_file.exists():
        content = (
            AFIK_YAML_TEMPLATE
            .replace("{project_slug}", slug)
            .replace("{description}", json.dumps(description, ensure_ascii=False))
        )
        yaml_file.write_text(content, encoding="utf-8")

    # 2. main.py
    main_file = project_dir / "main.py"
    if not main_file.exists():
        content = MAIN_PY_TEMPLATE.replace("{project_title}", title)
        main_file.write_text(content, encoding="utf-8")

    # 3. assets folders
    (project_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)
    (project_dir / "assets" / "icons").mkdir(parents=True, exist_ok=True)
    gitkeep_img = project_dir / "assets" / "images" / ".gitkeep"
    if not gitkeep_img.exists():
        gitkeep_img.touch()
    gitkeep_ico = project_dir / "assets" / "icons" / ".gitkeep"
    if not gitkeep_ico.exists():
        gitkeep_ico.touch()

    # 4. .gitignore
    gitignore_file = project_dir / ".gitignore"
    if not gitignore_file.exists():
        gitignore_file.write_text(GITIGNORE_TEMPLATE, encoding="utf-8")

    # 5. README.md
    readme_file = project_dir / "README.md"
    if not readme_file.exists():
        content = README_TEMPLATE.replace("{project_title}", title)
        readme_file.write_text(content, encoding="utf-8")

    return project_dir
