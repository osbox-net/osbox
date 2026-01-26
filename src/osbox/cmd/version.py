from importlib import metadata
import sys
from osbox.manifest import Manifest


def main():
    manifest = Manifest()
    print(f"python: {sys.version.split()[0]}")
    print(f"openstack: {manifest.manifest['requirements']['ref']}")
    for service_name, service_info in manifest.manifest["services"].items():
        try:
            version = metadata.version(service_name)
        except metadata.PackageNotFoundError:
            version = "not installed"
        print(f"{service_name}: {version} ({service_info['ref']})")