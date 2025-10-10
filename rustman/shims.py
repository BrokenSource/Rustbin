import os
import sys
from typing import NoReturn

from rustman import binary


def _shim(proxy: str) -> NoReturn:
    args = (proxy, *sys.argv[1:])

    # Windows creates a new process with execv, replacing
    # the current one, so we hold python until done.
    #
    # Surprisingly, it is smart enough to notice the rustup
    # binary file without .exe extension is an executable!
    if os.name == "nt":
        import subprocess
        sys.exit(subprocess.run(
            executable=binary(),
            args=args,
        ).returncode)

    # Replaces the current process
    os.execv(binary(), args)

def init() -> NoReturn:
    _shim("rustup-init")

def cargo() -> NoReturn:
    _shim("cargo")

def cargo_clippy() -> NoReturn:
    _shim("cargo-clippy")

def cargo_fmt() -> NoReturn:
    _shim("cargo-fmt")

def cargo_miri() -> NoReturn:
    _shim("cargo-miri")

def clippy_driver() -> NoReturn:
    _shim("clippy-driver")

def rls() -> NoReturn:
    _shim("rls")

def rust_analyzer() -> NoReturn:
    _shim("rust-analyzer")

def rust_gdb() -> NoReturn:
    _shim("rust-gdb")

def rust_gdbgui() -> NoReturn:
    _shim("rust-gdbgui")

def rust_lldb() -> NoReturn:
    _shim("rust-lldb")

def rustc() -> NoReturn:
    _shim("rustc")

def rustdoc() -> NoReturn:
    _shim("rustdoc")

def rustfmt() -> NoReturn:
    _shim("rustfmt")
