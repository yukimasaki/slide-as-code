#!/usr/bin/env python3
"""Create a slide directory outside Git repositories and print its HTML path."""

import argparse
import json
import os
from pathlib import Path
import sys


def absolute_path(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty path string")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute or start with ~/")
    return path.resolve()


def xdg_directory(variable, fallback):
    value = os.environ.get(variable)
    if not value:
        return Path.home() / fallback
    if not Path(value).is_absolute():
        raise ValueError(f"{variable} must be an absolute path")
    return Path(value).resolve()


def output_directory():
    config = xdg_directory("XDG_CONFIG_HOME", ".config") / "slide-as-code/config.json"
    if config.exists() or config.is_symlink():
        with config.open(encoding="utf-8") as stream:
            settings = json.load(stream)
        if not isinstance(settings, dict):
            raise ValueError("config.json must contain a JSON object")
        if "outputDir" in settings:
            return absolute_path(settings["outputDir"], "outputDir")
    return xdg_directory("XDG_DATA_HOME", ".local/share") / "slide-as-code"


def reject_repository(path):
    for directory in (path, *path.parents):
        if (directory / ".git").exists():
            raise ValueError("output must be outside Git repositories")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="one directory name for the slides")
    args = parser.parse_args()
    name = args.name
    if (
        not name.strip()
        or name in {".", "..", ".git"}
        or "/" in name
        or "\\" in name
        or any(ord(character) < 32 or ord(character) == 127 for character in name)
    ):
        parser.error("--name must be a single directory name without path separators")
    try:
        directory = (output_directory() / name).resolve()
        target = directory / "index.html"
        reject_repository(directory)
        if target.is_symlink():
            raise ValueError("index.html must not be a symbolic link")
        if target.exists() and not target.is_file():
            raise ValueError("index.html must be a regular file")
        directory.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"output_path: {error}", file=sys.stderr)
        return 1
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
