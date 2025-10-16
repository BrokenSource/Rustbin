"""
This file is both a hatchling hook and a build script
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from attrs import define
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from requests_cache import CachedSession


class Dirs:

    package: Path = Path(__file__).parent
    """Path to the package source root"""

    project: Path = package.parent
    """Path to the project root"""

    build: Path = project/"target"
    """Rust build directory"""

    # Fixme: Can hatchling provide a tempdir for us?
    temp: Path = Path(tempfile.gettempdir())

# Global requests session
SESSION = CachedSession(
    cache_name=Dirs.temp/"rustup.sqlite",
    expire_after=24*3600
)

# All available rustup shims
SHIMS: list[str] = [
    "cargo",
    "cargo-clippy",
    "cargo-fmt",
    "cargo-miri",
    "clippy-driver",
    "rls",
    "rust-analyzer",
    "rust-gdb",
    "rust-gdbgui",
    "rust-lldb",
    "rustc",
    "rustdoc",
    "rustfmt",
]

# ---------------------------------------------------------------------------- #
# Common code

class Environment:
    version: str = "RUSTMAN_VERSION"
    triple:  str = "RUSTMAN_TRIPLE"
    toolch:  str = "RUSTMAN_TOOLCHAIN"
    suffix:  str = "RUSTMAN_SUFFIX"
    wheel:   str = "RUSTMAN_WHEEL"

@define
class Target:

    version: str = os.environ.get(Environment.version, "1.28.2")
    """Rustup version https://github.com/rust-lang/rustup/tags"""

    triple: str = os.environ.get(Environment.triple, "")
    """Platform https://doc.rust-lang.org/nightly/rustc/platform-support.html"""

    toolch: str = os.environ.get(Environment.toolch, None)
    """Rustup toolchain to compile the shims with, defaults to 'triple'"""

    suffix: str = os.environ.get(Environment.suffix, "")
    """File suffix https://doc.rust-lang.org/std/env/consts/index.html"""

    wheel: str = os.environ.get(Environment.wheel, "none")
    """Platform https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/"""

    def __attrs_post_init__(self):
        self.toolch = (self.toolch or self.triple)

        # Idea: Infer options from the host? but needs working rustup..
        for (name, value) in (
            (Environment.version, self.version),
            (Environment.triple,  self.triple),
            (Environment.toolch,  self.toolch),
            (Environment.wheel,   self.wheel),
        ):
            if not bool(value):
                raise RuntimeError((
                    f"Missing {name} variable, source installations of rustman "
                    "require manual and explicit target configuration"
                ))

    def exe(self, name: str) -> str:
        """Get a platform specific executable name"""
        return f"{name}{self.suffix}"

    def export(self) -> None:
        """Export configuration to environment"""
        os.environ.update({
            Environment.version: self.version,
            Environment.triple:  self.triple,
            Environment.toolch:  self.toolch,
            Environment.suffix:  self.suffix,
            Environment.wheel:   self.wheel,
        })

    @property
    def rustup_url(self) -> str:
        """Download link for rustup"""
        return "/".join((
            "https://static.rust-lang.org/rustup/archive",
            self.version, self.triple,
            f"rustup-init{self.suffix}"
        ))

    def rustup_bytes(self) -> bytes:
        """Cached contents of a rustup download"""
        if (response := SESSION.get(self.rustup_url)).status_code != 200:
            raise RuntimeError(f"Failed to download {self.rustup_url}")
        return response.content

    def tempfile(self, name: str) -> Path:
        """Ephemeral path for packaging a file"""
        return Dirs.temp/f"{name}-{self.triple}-v{self.version}{self.suffix}"

    def download(self) -> Path:
        path = self.tempfile("rustup")
        path.write_bytes(self.rustup_bytes())
        path.chmod(0o755)
        return path

# ---------------------------------------------------------------------------- #
# Hatchling build hook

class BuildHook(BuildHookInterface):
    def initialize(self, version: str, build: dict) -> None:
        self.target = Target()

        # ---------------------------- #
        # Bundle rustup

        rustup: Path = self.target.download()

        # Pack rustup in the venv bin directory
        build["shared_scripts"][str(rustup)] = self.target.exe("rustup-init")
        build["tag"] = f"py3-none-{self.target.wheel}"
        build["pure_python"] = False

        # ---------------------------- #
        # Build rust shims

        # Build the rust project, chicken and egg problem!
        subprocess.run(("rustup", "target", "add", self.target.toolch))
        subprocess.check_call((
            "cargo", "zigbuild", "--release",
            "--manifest-path", Dirs.project/"Cargo.toml",
            "--target", self.target.toolch,
            "--target-dir", Dirs.build,
        ), cwd=Dirs.project)

        # Find the compiled binary
        compiled = Dirs.build/self.target.toolch/"release"/self.target.exe("rustman")

        # Pack all shims in the package
        for name in SHIMS:
            ephemeral = self.target.tempfile(name)
            ephemeral.write_bytes(compiled.read_bytes())
            build["shared_scripts"][str(ephemeral)] = self.target.exe(name)

    # Cleanup temporary files
    def finalize(self, *ig, **nore) -> None:
        for name in (*SHIMS, "rustup"):
            os.remove(self.target.tempfile(name))

# --------------------------------------------------------------------------- #
# Build script

TARGETS: tuple[Target] = (

    # Linux

    Target(
        triple="x86_64-unknown-linux-gnu",
        wheel="manylinux_2_17_x86_64"
    ),
    Target(
        triple="aarch64-unknown-linux-gnu",
        wheel="manylinux_2_17_aarch64"
    ),

    # MacOS

    Target(
        triple="x86_64-apple-darwin",
        wheel="macosx_10_9_x86_64"
    ),
    Target(
        triple="aarch64-apple-darwin",
        wheel="macosx_11_0_arm64"
    ),

    # Windows

    Target(
        triple="x86_64-pc-windows-gnu",
        wheel="win_amd64",
        suffix=".exe"
    ),

    # Works, awaiting general adoption
    # Target(
    #     triple="aarch64-pc-windows-msvc",
    #     toolch="aarch64-pc-windows-gnullvm",
    #     wheel="win_arm64",
    #     suffix=".exe"
    # ),
)

if __name__ == '__main__':
    for target in TARGETS:
        target.export()
        subprocess.check_call(
            cwd=Dirs.project,
            args=(
                sys.executable, "-m", "uv",
                "build", "--wheel",
            )
        )
