from pathlib import Path


def binary() -> Path:
    """Path to the bundled rustup binary"""
    return Path(__file__).parent/"rustup-init"
