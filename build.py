"""
This file is both the hatchling build hook and the build script run directly.
"""
import os
import platform
import subprocess
import sys
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Self

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from packaging.version import Version

TEMPDIR: Path = Path(tempfile.gettempdir())
PACKAGE: Path = Path(__file__).parent

# ---------------------------------------------------------------------------- #
# Common code

class Variables:
    target: str = "TARGET"
    shim:   str = "SHIM"

class System(str, Enum):
    Linux:   str = "linux"
    Windows: str = "windows"
    MacOS:   str = "macos"
    BSD:     str = "bsd"

    @classmethod
    def _missing_(cls, value: Any):
        if value in ("win32", "win", "windows", "cygwin"):
            return System.Windows
        if value in ("darwin", "macos", "osx"):
            return System.MacOS
        if value in ("bsd", "freebsd", "openbsd", "netbsd"):
            return System.BSD
        return None

    def executable(self) -> str:
        if self is self.Windows:
            return ".exe"
        return ""

# Todo: don't undestand ppc, s390x, riscv, armv*
class Arch(str, Enum):
    AMD32: str = "amd32"
    AMD64: str = "amd64"
    ARM32: str = "arm32"
    ARM64: str = "arm64"

    @classmethod
    def _missing_(cls, value: object):
        if value in ("x86_64", "x86-64"):
            return Arch.AMD64
        elif value in ("x86", "i686"):
            return Arch.AMD32
        return None

class Platform(str, Enum):
    LinuxAMD64:   str = "linux-amd64"
    LinuxARM64:   str = "linux-arm64"
    MacosAMD64:   str = "macos-amd64"
    MacosARM64:   str = "macos-arm64"
    WindowsAMD64: str = "windows-amd64"
    WindowsARM64: str = "windows-arm64"

    @staticmethod
    def from_parts(system: System, arch: Arch) -> Optional[Self]:
        return Platform(f"{system.value}-{arch.value}")

    @property
    def system(self) -> System:
        return System(self.value.split("-")[0])

    @property
    def arch(self) -> Arch:
        return Arch(self.value.split("-")[1])

    def triple(self,
        msvc: bool=True,
        musl: bool=False,
    ) -> Optional[str]:
        """Get the Rust target triple"""
        return {
            self.WindowsAMD64: "x86_64-pc-windows-"  + ("msvc" if msvc else "gnu"),
            self.WindowsARM64: "aarch64-pc-windows-" + ("msvc" if msvc else "gnullvm"),
            self.LinuxAMD64:   "x86_64-unknown-linux-gnu",
            self.LinuxARM64:   "aarch64-unknown-linux-gnu",
            self.MacosAMD64:   "x86_64-apple-darwin",
            self.MacosARM64:   "aarch64-apple-darwin",
        }.get(self, None)

    def wheel_tag(self) -> Optional[str]:
        """Get the Python platform wheel tag"""
        return {
            self.WindowsAMD64: "win_amd64",
            self.WindowsARM64: "win_arm64",
            self.LinuxAMD64:   "manylinux_2_17_x86_64",
            self.LinuxARM64:   "manylinux_2_17_aarch64",
            self.MacosAMD64:   "macosx_10_9_x86_64",
            self.MacosARM64:   "macosx_11_0_arm64",
        }.get(self, None)

# ---------------------------------------------------------------------------- #
# Hatchling build hook

class BuildHook(BuildHookInterface):
    def initialize(self, version: str, build: dict) -> None:
        from requests_cache import CachedSession

        # This python package follows rustup versioning with
        # an extra sub-micro number for unique self releases
        version = Version(self.metadata.version)

        # Get a custom build target or current host platform
        if (target := os.environ.get(Variables.target)):
            target = Platform(target.lower())
        else:
            target = Platform.from_parts(
                system=System(platform.system().lower()),
                arch=Arch(platform.machine().lower()),
            )

        # Make the download URL
        rustup_path = TEMPDIR/"rustup.bin"
        rustup_url = "/".join((
            "https://static.rust-lang.org/rustup/archive",
            f"{version.major}.{version.minor}.{version.micro}",
            target.triple(),
            f"rustup-init{target.system.executable()}",
        ))

        with CachedSession(
            cache_name=TEMPDIR/"rustup.sqlite",
            expire_after=24*3600,
        ) as session:
            response = session.get(rustup_url)

            if response.status_code != 200:
                raise RuntimeError(f"Failed to download rustup from {rustup_url}")

            rustup_path.write_bytes(response.content)
            rustup_path.chmod(0o755)

        # Pack rustup in the venv bin directory
        build["shared_scripts"][str(rustup_path)] = f"rustup-init{target.system.executable()}"
        build["tag"] = f"py3-none-{target.wheel_tag()}"
        build["pure_python"] = False

# ---------------------------------------------------------------------------- #
# Build script

if __name__ == '__main__':
    for target in Platform:
        print(f"Building for {target}")

        os.environ[Variables.target] = target.value

        if call := subprocess.run((
            sys.executable, "-m", "uv",
            "build", "--wheel",
        )).returncode != 0:
            raise RuntimeError(f"Build failed for {target}")

