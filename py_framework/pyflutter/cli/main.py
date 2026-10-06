"""
PyFlutter CLI entry point.
Commands:
  pyflutter run [path/to/main.py] [-d <device>]
  pyflutter devices
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure py_framework is on sys.path if run directly as a script
_framework_dir = Path(__file__).resolve().parents[2]
if str(_framework_dir) not in sys.path:
    sys.path.insert(0, str(_framework_dir))

from pyflutter import __version__
from pyflutter.cli.devices import list_devices
from pyflutter.cli.runner import PyFlutterRunner


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pyflutter",
        description="PyFlutter - The ultra-fast Python to Flutter Bridge Framework",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"PyFlutter {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # `pyflutter run`
    run_parser = subparsers.add_parser("run", help="Run a PyFlutter application in debug mode")
    run_parser.add_argument(
        "entrypoint",
        nargs="?",
        default="main.py",
        help="Path to Python app entrypoint file (default: main.py)",
    )
    run_parser.add_argument(
        "-d", "--device",
        dest="device_id",
        help="Target device id or name (e.g. windows, chrome, or phone ID)",
    )
    run_parser.add_argument(
        "-p", "--port",
        type=int,
        default=7879,
        help="TCP port for the Rust-to-Flutter bridge (default: 7879)",
    )
    run_parser.add_argument(
        "--attach",
        action="store_true",
        help="Attach to an already running Flutter instance without launching a new one",
    )

    # `pyflutter devices`
    subparsers.add_parser("devices", help="List all detected Flutter devices")

    # `pyflutter add <package>`
    add_parser = subparsers.add_parser("add", help="Install a native Flutter package into the runtime")
    add_parser.add_argument(
        "package",
        help="Name of the Flutter package to install (e.g. url_launcher, shared_preferences)",
    )

    # `pyflutter remove <package>`
    remove_parser = subparsers.add_parser("remove", help="Uninstall a native Flutter package from the runtime")
    remove_parser.add_argument(
        "package",
        help="Name of the Flutter package to remove",
    )

    # `pyflutter plugin list|new <package>`
    plugin_parser = subparsers.add_parser("plugin", help="Inspect the plugin catalog or scaffold a new plugin mapping")
    plugin_sub = plugin_parser.add_subparsers(dest="plugin_command", required=True)
    plugin_sub.add_parser("list", help="List catalog plugins and which ones this project uses")
    plugin_new = plugin_sub.add_parser("new", help="Create the shim, Python module and test for a new package")
    plugin_new.add_argument("package", help="pub.dev package name (lowercase, underscores)")

    # `pyflutter create <name>`
    create_parser = subparsers.add_parser("create", help="Create a new PyFlutter project directory with Material 3 template")
    create_parser.add_argument(
        "name",
        help="Name of the project to create (e.g. my_shop, my_cool_app)",
    )
    create_parser.add_argument(
        "--description", "-d",
        default="A modern mobile application powered by PyFlutter",
        help="Short description for the project manifest",
    )

    # `pyflutter init`
    init_parser = subparsers.add_parser("init", help="Initialize a PyFlutter project in the current directory")
    init_parser.add_argument(
        "--description", "-d",
        default="A modern mobile application powered by PyFlutter",
        help="Short description for the project manifest",
    )

    # `pyflutter sync`
    subparsers.add_parser("sync", help="Synchronize pyflutter.yaml permissions to AndroidManifest.xml and Info.plist")

    # `pyflutter build <target>`
    build_parser = subparsers.add_parser("build", help="Build an autonomous standalone package (apk, appbundle, windows, etc.)")
    build_parser.add_argument(
        "target",
        nargs="?",
        default="apk",
        choices=["apk", "appbundle", "bundle", "ipa", "ios", "windows", "linux", "macos", "web"],
        help="Target build format (default: apk)",
    )
    build_parser.add_argument(
        "entrypoint",
        nargs="?",
        default="main.py",
        help="Path to Python app entrypoint file (default: main.py)",
    )
    build_parser.add_argument(
        "--mode",
        choices=["debug", "release", "profile"],
        default=None,
        help="Build mode: debug, release, or profile (default: debug)",
    )
    mode_group = build_parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--release",
        action="store_true",
        help="Build in release mode",
    )
    mode_group.add_argument(
        "--debug",
        action="store_true",
        help="Build in debug mode (default)",
    )
    mode_group.add_argument(
        "--profile",
        action="store_true",
        help="Build in profile mode",
    )
    build_parser.add_argument(
        "--split-per-abi",
        action="store_true",
        help="Split the APK per ABI for smaller download size",
    )

    return parser.parse_args(argv)


def handle_devices():
    devices = list_devices()
    if not devices:
        print("No supported devices found. Make sure Flutter SDK is installed and devices are connected.")
        return
    print(f"\nFound {len(devices)} available device(s):")
    for d in devices:
        name = d.get("name", "Unknown")
        dev_id = d.get("id", "")
        target = d.get("targetPlatform", "")
        sdk = d.get("sdk", "")
        print(f"  - {name} (ID: {dev_id}) | Platform: {target} | SDK: {sdk}")
    print()


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    if args.command == "devices":
        handle_devices()
        sys.exit(0)

    if args.command == "add":
        from pyflutter.cli import plugins_cmd
        sys.exit(0 if plugins_cmd.add(args.package) else 1)

    if args.command == "remove":
        from pyflutter.cli import plugins_cmd
        sys.exit(0 if plugins_cmd.remove(args.package) else 1)

    if args.command == "plugin":
        from pyflutter.cli import plugins_cmd
        if args.plugin_command == "list":
            plugins_cmd.list_plugins()
            sys.exit(0)
        sys.exit(0 if plugins_cmd.new(args.package) else 1)

    if args.command == "create":
        from pyflutter.cli.creator import create_project, sanitize_project_name
        target_dir = Path.cwd() / sanitize_project_name(args.name)
        if target_dir.exists() and any(target_dir.iterdir()):
            print(f"❌ Error: Directory '{target_dir.name}' already exists and is not empty.")
            sys.exit(1)
        created_path = create_project(
            project_dir=target_dir,
            name=args.name,
            description=args.description,
        )
        print(f"\n🎉 Successfully created PyFlutter project '{args.name}' at:\n   {created_path}\n")
        print("Next steps:")
        print(f"  cd {target_dir.name}")
        print("  pyflutter run\n")
        sys.exit(0)

    if args.command == "init":
        from pyflutter.cli.creator import create_project
        created_path = create_project(
            project_dir=Path.cwd(),
            name=Path.cwd().name,
            description=args.description,
        )
        print(f"\n✅ PyFlutter project initialized in current directory:\n   {created_path}\n")
        print("To run the application:")
        print("  pyflutter run\n")
        sys.exit(0)

    if args.command == "sync":
        from pyflutter.core.config import PyFlutterConfig
        from pyflutter.cli.runner import find_workspace_root
        from pyflutter.core.runtime_project import ProjectRuntime
        from pyflutter.plugins.catalog import CatalogError, prepare_runtime
        config = PyFlutterConfig.find_and_load(Path.cwd())
        runtime = ProjectRuntime.for_config(config, find_workspace_root() / "dart_runtime", Path.cwd())
        try:
            prepare_runtime(runtime, config)
        except CatalogError as e:
            print(f"Error: {e}")
            sys.exit(1)
        print("Plugins and native manifests (Android & iOS) synchronized with pyflutter.yaml")
        sys.exit(0)

    if args.command == "run":
        entrypoint_path = Path(args.entrypoint).resolve()
        if not entrypoint_path.exists():
            # If not found directly, check examples directory
            candidate = Path.cwd() / "examples" / args.entrypoint
            if candidate.exists():
                entrypoint_path = candidate
            else:
                print(f"Error: Entrypoint file '{args.entrypoint}' does not exist.")
                sys.exit(1)

        runner = PyFlutterRunner(
            entrypoint=entrypoint_path,
            device_id=args.device_id,
            port=args.port,
            attach_only=args.attach,
        )
        runner.start()
        return

    if args.command == "build":
        from pyflutter.cli.builder import PyFlutterBuilder
        flag_mode = "release" if args.release else "profile" if args.profile else "debug" if args.debug else None
        if flag_mode and args.mode and flag_mode != args.mode:
            print(f"Error: conflicting build modes: --{flag_mode} and --mode {args.mode}.")
            sys.exit(2)
        build_mode = flag_mode or args.mode or "debug"
        builder = PyFlutterBuilder(
            target=args.target,
            entrypoint=args.entrypoint,
            release=(build_mode == "release"),
            split_per_abi=args.split_per_abi,
            profile=(build_mode == "profile"),
        )
        success = builder.build()
        sys.exit(0 if success else 1)



if __name__ == "__main__":
    main()
