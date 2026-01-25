#!/usr/bin/env python3

import os
import json
import tempfile
from pathlib import Path
import subprocess
import shutil


def run_cmd(cmd: str, cwd: Path):
    build_env = os.environ.copy()
    if "PYTHONPATH" in build_env:
        del build_env["PYTHONPATH"]
    if "VIRTUAL_ENV" in build_env:
        del build_env["VIRTUAL_ENV"]

    del build_env["PATH"]
    for key in list(build_env.keys()):
        if key.startswith("UV_"):
            del build_env[key]
    
    paths = os.environ.get("PATH", "").split(os.pathsep)
    new_paths: list[str] = []
    for p in paths:
        if "venv" in p:
            continue
        new_paths.append(p)

    build_env["PATH"] = os.pathsep.join(new_paths)

    process = subprocess.Popen(cmd, cwd=cwd, shell=True, env=build_env)
    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")


def build_openstack():

    root_path = Path(__file__).parent.resolve()
    dist_path = root_path / "dist"
    dist_path.mkdir(parents=True, exist_ok=True)

    print(f"Starting build of OpenStack wheelhouse from {root_path}")

    with open("src/osbox/manifest.json", "r") as f:
        manifest = json.load(f)

    with tempfile.TemporaryDirectory() as td:
        build_path = Path(td)
        print(f"Building in temporary directory: {build_path}")

        # clone the requirements
        print(f"Cloning requirements @ {manifest['requirements']['ref']}")
        run_cmd(
            f"git clone {manifest['requirements']['src']} -b {manifest['requirements']['ref']}",
            cwd=build_path,
        )
        # copy upper-constraints.txt to build_path/requirements
        req_src = build_path / "requirements" / "upper-constraints.txt"
        req_dst = dist_path / "upper-constraints.txt"
        shutil.copy(req_src, req_dst)
        print(f"Copied upper-constraints.txt to {req_dst}")

        for service_name, service_info in manifest["services"].items():
            print(f"Building service: {service_name} @ {service_info['ref']}")
            service_path = build_path / service_name
            service_path.mkdir(parents=True, exist_ok=True)

            # clone the repo
            run_cmd(
                f"git clone {service_info['src']} {service_path}",
                cwd=build_path,
            )

            # checkout the specified ref
            run_cmd(
                f"git checkout {service_info['ref']}",
                cwd=service_path,
            )

            # create venv
            run_cmd(
                "uv venv",
                cwd=service_path,
            )

            # install requirements
            run_cmd(
                "uv pip install -r requirements.txt -c ../requirements/upper-constraints.txt",
                cwd=service_path,
            )

            # build the service
            run_cmd(
                "uv build",
                cwd=service_path,
            )

            # copy the built artifact back to root_path/dist
            built_files = list((service_path / "dist").glob("*.whl"))
            for bf in built_files:
                # install into the venv to verify
                run_cmd(
                    f"uv pip install {bf} -c ../requirements/upper-constraints.txt",
                    cwd=service_path,
                )
                # copy to dist
                shutil.copy(bf, dist_path)
                print(f"Copied {bf} to {dist_path}")

            # copy assets
            for asset in service_info.get("assets", []):
                asset_src = service_path / asset["src"]
                asset_dst = root_path / "src" / "osbox" / "assets" / service_name / asset["name"]
                asset_dst.parent.mkdir(parents=True, exist_ok=True)

                if asset.get("genconfig", False):
                    run_cmd(
                        f"uv run oslo-config-generator --config-file {asset_src} --output-file {asset_dst}",
                        cwd=service_path,
                    )
                elif asset.get("genpolicy", False):
                    run_cmd(
                        f"uv run oslopolicy-sample-generator --config-file {asset_src} --output-file {asset_dst}",
                        cwd=service_path,
                    )
                else:
                    if asset_src.is_dir():
                        shutil.copytree(asset_src, asset_dst, dirs_exist_ok=True)
                    else:
                        shutil.copy(asset_src, asset_dst)
                
                print(f"Copied asset {asset['name']}")

        print("Build of OpenStack wheelhouse completed.")


def build_osbox():

    root_path = Path(__file__).parent.resolve()
    dist_path = root_path / "dist"
    dist_path.mkdir(parents=True, exist_ok=True)

    print(f"Starting build of osbox from {root_path}")

    print("Building osbox wheel...")
    run_cmd(
        "uv build --wheel",
        cwd=root_path,
    )
    built_file = list((root_path / "dist").glob("osbox*.whl"))[0]
    print(f"Built osbox wheel file: {built_file}")

    with tempfile.TemporaryDirectory() as td:
        build_path = Path(td)
        print(f"Building in temporary directory: {build_path}")

        # copy entrypoint and spec file
        for f in ["main.py", "osbox.spec"]:
            src = root_path / f
            dst = build_path / f
            shutil.copy(src, dst)
            print(f"Copied {f} to build path: {dst}")
        
        # create venv
        run_cmd(
            "uv venv",
            cwd=build_path,
        )

        # install dist wheels
        all_wheels = list(dist_path.glob("*.whl"))
        wheel_files = " ".join(str(wheel) for wheel in all_wheels)
        run_cmd(
            f"uv pip install {wheel_files} -c {dist_path / 'upper-constraints.txt'}",
            cwd=build_path,
        )

        # build osbox executable
        run_cmd(
            "uv pip install pyinstaller",
            cwd=build_path,
        )
        run_cmd(
            "uv run pyinstaller --noconfirm osbox.spec",
            cwd=build_path,
        )

        # copy the built executable back to root_path/dist
        built_exe = build_path / "dist" / "osbox"
        final_exe = dist_path / "osbox"
        shutil.copy(built_exe, final_exe)
        print(f"Copied built osbox executable to {final_exe}")


if __name__ == "__main__":
    build_openstack()
    build_osbox()
