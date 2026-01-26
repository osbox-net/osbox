import json
from pathlib import Path
from typing import TypedDict, NotRequired
from osbox.wsgi import wsgi_server
from osbox.command import command


class ServiceCommand(TypedDict):
    name: str
    module: str
    wsgi_server: NotRequired[bool | None]
    factory: NotRequired[bool | None]
    port: NotRequired[int | None]


class Manifest:
    def __init__(self):
        # load manifest from package
        manifest_file = Path(__file__).parent / "manifest.json"
        self.manifest = json.loads(manifest_file.read_text())

        # make command mapping
        self.command_map: dict[str, ServiceCommand] = {}
        for _, service_info in self.manifest["services"].items():
            for command in service_info.get("commands", []):
                self.command_map[command["name"]] = command

    @property
    def commands(self) -> list[str]:
        return list(self.command_map.keys())
    
    def has_command(self, command_name: str) -> bool:
        return command_name in self.command_map

    def run(self, command_name: str) -> None:
        command_info = self.command_map.get(command_name)
        if not command_info:
            raise ValueError(f"Unknown command: {command_name}")

        if command_info.get("wsgi_server"):
            fn = wsgi_server(
                app_spec=command_info["module"],
                service=command_name,
                port=command_info.get("port", 8000),
                factory=command_info.get("factory", False),
            )
        else:
            fn = command(command_info["module"])

        return fn()
