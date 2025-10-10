import shutil


# Fixme: Can we assume venv is properly activated?
def binary() -> str:
    """Path to the bundled rustup binary"""
    return shutil.which("rustup-init")
