from __future__ import annotations
import os
from gunicorn.app.base import BaseApplication
from gunicorn.util import import_app


def wsgi_server(app_spec: str, service: str, port: int, *, factory: bool = False):
    service_env_slug = service.upper().replace("-", "_")
    def run() -> None:
        bind = os.environ.get(f"OSBOX_{service_env_slug}_BIND", f"127.0.0.1:{port}")
        WSGIServer(
            app_spec,
            {
                "bind": bind,
                "workers": int(
                    os.environ.get(
                        "OSBOX_WORKERS",
                        int(os.environ.get(f"OSBOX_{service_env_slug}_WORKERS", "1")),
                    )
                ),
                "timeout": 300,
                "threads": int(
                    os.environ.get(
                        "OSBOX_THREADS",
                        int(os.environ.get(f"OSBOX_{service_env_slug}_THREADS", "1")),
                    )
                ),
                "accesslog": "-",
                "errorlog": "-",
                "loglevel": "info",
                "worker_class": "sync",
                "preload_app": False,
                "factory": factory,
            },
        ).run()

    return run


class WSGIServer(BaseApplication):
    def __init__(self, application, options=None):
        self.application = application  # can be callable OR "module:obj"
        self.options = options or {}
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if value is not None:
                self.cfg.set(key, value)

    def load(self):
        # If passed "module:obj", import it inside the worker process.
        if isinstance(self.application, str):
            obj = import_app(self.application)

            # If configured as a factory, call it to get the WSGI app.
            if getattr(self.cfg, "factory", False):
                return obj()

            return obj

        # Otherwise assume it's already a WSGI callable
        return self.application
