import importlib


def load_object(spec: str):
    mod, attr = spec.split(":", 1)
    return getattr(importlib.import_module(mod), attr)


def command(spec: str):
    def run() -> None:
        fn = load_object(spec)
        fn()

    return run
