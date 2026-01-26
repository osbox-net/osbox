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


def cmd_asset_cat(service_name: str, asset_name: str):
    assets_dir = Path(__file__).parent.parent / "assets"
    asset_path = assets_dir / service_name / asset_name

    if not asset_path.exists() or not asset_path.is_file():
        print(f"Asset not found: {service_name}/{asset_name}")
        sys.exit(1)

    with asset_path.open("r", encoding="utf-8") as f:
        content = f.read()
        sys.stdout.write(content)
        if content and not content.endswith("\n"):
            sys.stdout.write("\n")

    
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

    cat_parser = subparsers.add_parser(
        "cat",
        help="Print an asset to stdout",
        description="Print a specific asset file to stdout",
    )
    cat_parser.add_argument("service_name", help="Service the asset belongs to")
    cat_parser.add_argument("asset_name", help="Asset filename to print")

    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    if args.command == "list":
        cmd_asset_list(service_name=args.service_name)
    elif args.command == "cat":
        cmd_asset_cat(service_name=args.service_name, asset_name=args.asset_name)
    else:
        parser.error(f"Unknown command: {args.command}")