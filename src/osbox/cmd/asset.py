from pathlib import Path
import argparse
import sys


def cmd_asset_list(service_name: str | None = None):
    assets_dir = Path(__file__).parent.parent / "assets"
    
    if service_name:
        list_dir = assets_dir / service_name
        if not list_dir.exists() or not list_dir.is_dir():
            print(f"Unknown service or no assets for service: {service_name}")
            sys.exit(1)

    for service_dir in assets_dir.iterdir():
        if service_name and service_dir.name != service_name:
            continue
        if service_dir.is_dir():
            print(f"{service_dir.name}")
            for asset_file in service_dir.iterdir():
                if asset_file.is_file():
                    print(f"  {asset_file.name}")

    
def main():
    parser = argparse.ArgumentParser(prog="osbox asset")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list",
        help="List assets for a service or all services",
        description="List assets for a service or all services",
    )
    list_parser.add_argument(
        "service_name",
        nargs="?",
        help="Name of the service to list assets for (optional)",
    )

    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    if args.command == "list":
        cmd_asset_list(service_name=args.service_name)
    else:
        parser.error(f"Unknown command: {args.command}")