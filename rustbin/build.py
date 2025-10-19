"""This file is both a hatchling hook and a build script"""
import contextlib
import os
import subprocess
import tempfile
from pathlib import Path

from attrs import define
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.metadata.plugin.interface import MetadataHookInterface
from requests import Response
from requests_cache import CachedSession

__package__: str = "rustbin"
"""Package name, must match Cargo.toml [[bin]]"""

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
SESSION: CachedSession = CachedSession(
    cache_name=Dirs.temp/"rustup.sqlite",
    expire_after=24*3600
)

# All available rustup shims
SHIMS: list[str] = [
    "cargo-clippy",
    "cargo-fmt",
    "cargo-miri",
    "cargo",
    "clippy-driver",
    "rls",
    "rust-analyzer",
    "rust-gdb",
    "rust-gdbgui",
    "rust-lldb",
    "rustc",
    "rustdoc",
    "rustfmt",
    "rustup",
]

# ---------------------------------------------------------------------------- #
# Common code

class Environment:
    """Centralized variable names"""
    version: str = "RUSTBIN_VERSION"
    triple:  str = "RUSTBIN_TRIPLE"
    toolch:  str = "RUSTBIN_TOOLCHAIN"
    suffix:  str = "RUSTBIN_SUFFIX"
    wheel:   str = "RUSTBIN_WHEEL"
    zig:     str = "RUSTBIN_ZIG"

@define
class Target:

    version: str = os.environ.get(Environment.version, "1.28.2")
    """Rustup version https://github.com/rust-lang/rustup/tags"""

    triple: str = os.environ.get(Environment.triple, "")
    """Platform https://doc.rust-lang.org/nightly/rustc/platform-support.html"""

    toolch: str = os.environ.get(Environment.toolch, None)
    """Rustup toolchain to compile the shims with, defaults to 'triple'"""

    suffix: str = os.environ.get(Environment.suffix, "")
    """Executable suffix https://doc.rust-lang.org/std/env/consts/index.html"""

    wheel: str = os.environ.get(Environment.wheel, "none")
    """Platform https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/"""

    zig: bool = os.environ.get(Environment.zig, "1") == "1"
    """Use cargo-zigbuild to compile the rust shims"""

    def __attrs_post_init__(self):
        self.toolch = (self.toolch or self.triple)

    def exe(self, name: str) -> str:
        """Get a platform specific executable name"""
        return f"{name}{self.suffix}"

    def export(self) -> dict:
        """Export configuration as dict"""
        return {
            Environment.version: self.version,
            Environment.triple:  self.triple,
            Environment.toolch:  self.toolch,
            Environment.suffix:  self.suffix,
            Environment.wheel:   self.wheel,
            Environment.zig:     str(int(self.zig)),
        }

    @property
    def rustup_url(self) -> str:
        """Download url for rustup"""
        return "/".join((
            "https://static.rust-lang.org/rustup/archive",
            self.version, self.triple,
            f"rustup-init{self.suffix}"
        ))

    def rustup_bytes(self) -> bytes:
        """Cached contents of a rustup download"""
        response: Response = SESSION.get(self.rustup_url)

        if response.status_code != 200:
            raise RuntimeError(f"Failed to download {self.rustup_url} ({response.status_code})")

        return response.content

    def tempfile(self, name: str) -> Path:
        """Ephemeral unique path for packaging a file"""
        return Dirs.temp/f"{name}-{self.triple}-v{self.version}{self.suffix}"

    def download(self) -> Path:
        path = self.tempfile("rustup-init")
        path.write_bytes(self.rustup_bytes())
        path.chmod(0o755)
        return path

# ---------------------------------------------------------------------------- #
# Hatchling build hook

class MetadataHook(MetadataHookInterface):
    def update(self, metadata: dict) -> None:
        self.target = Target()

class BuildHook(BuildHookInterface):
    def initialize(self, version: str, build: dict) -> None:
        self.target = Target()

        # Make wheels always platform specific, any py3
        build["tag"] = f"py3-none-{self.target.wheel}"
        build["pure_python"] = False

        # No rustup requested or unset sdist
        if not self.target.triple:
            print(f"Warn: Missing {Environment.triple}, rustup will not be bundled")
            return None

        # ---------------------------- #
        # Bundle rustup

        # Pack rustup in the venv bin directory
        build["shared_scripts"][self.target.download()] = \
            self.target.exe("rustup-init")

        # ---------------------------- #
        # Build rust shims

        # Build fast shims, chicken and egg problem!
        subprocess.run(("rustup", "target", "add", self.target.toolch))
        subprocess.check_call((
            "cargo", ("zig"*self.target.zig + "build"), "--release",
            "--manifest-path", (Dirs.project/"Cargo.toml"),
            "--target", self.target.toolch,
            "--target-dir", Dirs.build,
        ), cwd=Dirs.project)

        # Find the compiled binary
        binary = Dirs.build.joinpath(
            self.target.toolch, "release",
            self.target.exe(__package__)
        )

        # Pack all shims in the package
        for name in SHIMS:
            shim = self.target.tempfile(name)
            shim.write_bytes(binary.read_bytes())
            build["shared_scripts"][str(shim)] = self.target.exe(name)

    # Cleanup temporary files
    def finalize(self, *ig, **nore) -> None:
        for name in (*SHIMS, "rustup"):
            with contextlib.suppress(FileNotFoundError):
                os.remove(self.target.tempfile(name))

# --------------------------------------------------------------------------- #
# Build script

# Note: Items are somewhat ordered by popularity
TARGETS: tuple[Target] = (

    # -------------------------------- #
    # Windows

    Target(
        triple="x86_64-pc-windows-gnu",
        wheel="win_amd64",
        suffix=".exe",
    ),
    Target(
        triple="aarch64-pc-windows-msvc",
        toolch="aarch64-pc-windows-gnullvm",
        wheel="win_arm64",
        suffix=".exe",
    ),

    # -------------------------------- #
    # Linux

    Target(
        triple="x86_64-unknown-linux-gnu",
        wheel="manylinux_2_17_x86_64",
    ),
    Target(
        triple="aarch64-unknown-linux-gnu",
        wheel="manylinux_2_17_aarch64",
    ),
    Target(
        triple="i686-unknown-linux-gnu",
        wheel="manylinux_2_17_i686",
    ),
    Target(
        triple="x86_64-unknown-linux-musl",
        wheel="musllinux_2_17_x86_64",
    ),

    # -------------------------------- #
    # MacOS

    Target(
        triple="aarch64-apple-darwin",
        wheel="macosx_11_0_arm64",
    ),
    Target(
        triple="x86_64-apple-darwin",
        wheel="macosx_10_9_x86_64",
    ),

    # -------------------------------- #
    # BSD

    # Fixme: Zigbuild unsupported
    # Target(
    #     triple="x86_64-unknown-freebsd",
    #     wheel="freebsd_12_0_x86_64",
    # ),
)

if __name__ == '__main__':
    for target in TARGETS:
        environ = dict(os.environ)
        environ.update(target.export())
        subprocess.check_call(
            args=("uv", "build", "--wheel"),
            cwd=Dirs.project,
            env=environ,
        )
    subprocess.check_call(
        args=("uv", "build", "--sdist"),
        cwd=Dirs.project,
    )
