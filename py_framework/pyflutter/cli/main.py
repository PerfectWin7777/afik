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

    # `pyflutter init`
    subparsers.add_parser("init", help="Initialize a new pyflutter.yaml project manifest in current directory")

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
        from pyflutter.plugins.manager import add_flutter_package
        success = add_flutter_package(args.package)
        sys.exit(0 if success else 1)

    if args.command == "remove":
        from pyflutter.plugins.manager import remove_flutter_package
        success = remove_flutter_package(args.package)
        sys.exit(0 if success else 1)

    if args.command == "init":
        from pyflutter.core.config import PyFlutterConfig
        target = Path.cwd() / "pyflutter.yaml"
        if target.exists():
            print(f"pyflutter.yaml already exists at {target}")
            sys.exit(0)
        config = PyFlutterConfig(
            name=Path.cwd().name.lower().replace("-", "_"),
            description="A new PyFlutter application",
            version="0.1.0",
            entrypoint="main.py",
            config_path=target,
        )
        config.save()
        print(f"✅ Created pyflutter.yaml project manifest at {target}")
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


if __name__ == "__main__":
    main()
