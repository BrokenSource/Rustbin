"""This file is both a hatchling hook and a build script"""

# /// script
# dependencies = [
#   "attrs",
#   "cargo-zigbuild",
#   "hatchling",
#   "requests-cache",
#   "requests",
#   "ziglang",
# ]
# ///

import contextlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import attrs
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from requests_cache import CachedSession

# Ensure ziglang binary can be found
with contextlib.suppress(ImportError):
    import ziglang
    _ziglang = Path(ziglang.__file__).parent
    os.environ["PATH"] += f"{os.pathsep}{_ziglang}"

class Dirs:

    package: Path = Path(__file__).parent
    """Path to the package source root"""

    project: Path = package.parent
    """Path to the project root"""

    build: Path = Path(os.getenv("CARGO_TARGET_DIR") or (project/"target"))
    """Rust build directory"""

    temp: Path = Path(tempfile.gettempdir())

RUSTBIN_TARGET: str = "RUSTBIN_TARGET"
"""Serde environment variable"""

SESSION: CachedSession = CachedSession(
    cache_name=Dirs.temp/"rustup.sqlite",
    expire_after=24*3600)
"""Global requests session"""

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

@attrs.define
class Target:

    version: str = "1.28.2"
    """Rustup version https://github.com/rust-lang/rustup/tags"""

    triple: str = ""
    """Platform https://doc.rust-lang.org/nightly/rustc/platform-support.html"""

    toolch: str = None # type: ignore
    """Rustup toolchain to compile the shims with, defaults to 'triple'"""

    suffix: str = ""
    """Executable suffix https://doc.rust-lang.org/std/env/consts/index.html"""

    wheel: str = "none"
    """Platform https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/"""

    zig: bool = True
    """Use cargo-zigbuild to compile the rust shims"""

    def __attrs_post_init__(self):
        self.toolch = (self.toolch or self.triple)

    def exe(self, name: str) -> str:
        """Get a platform specific executable name"""
        return f"{name}{self.suffix}"

    @property
    def rustup_url(self) -> str:
        return "/".join((
            "https://static.rust-lang.org/rustup/archive",
            self.version, self.triple,
            f"rustup-init{self.suffix}"
        ))

    def rustup_bytes(self) -> bytes:
        return SESSION.get(self.rustup_url).content

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

class BuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        self.target = Target(**json.loads(os.getenv(RUSTBIN_TARGET, r"{}")))

        # Skip source distributions
        if (not self.target.triple):
            print("Missing configuration, rustup will not be available")
            return None

        # Make wheels always platform specific, any py3
        build_data["tag"] = f"py3-none-{self.target.wheel}"
        build_data["pure_python"] = False

        # ---------------------------- #
        # Bundle rustup

        # Pack rustup in the venv bin directory
        build_data["shared_scripts"][self.target.download()] = \
            self.target.exe("rustup-init")

        # ---------------------------- #
        # Build rust shims

        # Build fast shims, chicken and egg problem!
        subprocess.run(("rustup", "set", "profile", "minimal"))
        subprocess.run(("rustup", "default", "stable"))
        subprocess.run(("rustup", "target", "add", self.target.toolch))
        subprocess.check_call((
            "cargo", ("zig"*self.target.zig + "build"), "--release",
            "--manifest-path", (Dirs.project/"Cargo.toml"),
            "--target", self.target.toolch,
            "--target-dir", Dirs.build,
        ), cwd=Dirs.project)

        # Find the compiled binary
        binary: bytes = Dirs.build.joinpath(
            self.target.toolch, "release",
            self.target.exe("rustbin")
        ).read_bytes()

        # Pack all shims in the package
        for name in SHIMS:
            shim = self.target.tempfile(name)
            shim.write_bytes(binary)
            build_data["shared_scripts"][str(shim)] = self.target.exe(name)

    # Cleanup temporary files
    def finalize(self, *ig, **nore) -> None:
        for name in (*SHIMS, "rustup"):
            with contextlib.suppress(FileNotFoundError):
                os.remove(self.target.tempfile(name))

# --------------------------------------------------------------------------- #
# Build script

# Note: Items are somewhat ordered by popularity
TARGETS: list[Target] = [

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

    # Target(
    #     triple="x86_64-unknown-freebsd",
    #     wheel="freebsd_12_0_x86_64",
    # ),
]

if __name__ == '__main__':
    for target in TARGETS:
        environ = os.environ.copy()
        environ[RUSTBIN_TARGET] = json.dumps(attrs.asdict(target))
        subprocess.check_call(
            args=("uv", "build", "--wheel"),
            cwd=Dirs.project,
            env=environ,
        )
    subprocess.check_call(
        args=("uv", "build", "--sdist"),
        cwd=Dirs.project,
    )
