import sys
import os
from osbox.manifest import Manifest


def main() -> None:
    manifest = Manifest()

    invoked_as = os.path.basename(sys.argv[0])

    # check if invoked as a command
    if manifest.has_command(invoked_as):
        sys.exit(manifest.run(invoked_as))
        return

    # otherwise first arg is the command
    sys.argv.pop(0)
    try:
        cmd = sys.argv[0]
    except IndexError:
        print(f"Usage: {invoked_as} <command> [args...]")
        print("Available commands:")
        for command in manifest.commands:
            print(f"  {command}")
        sys.exit(0)

    if not manifest.has_command(cmd):
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

    sys.exit(manifest.run(cmd))