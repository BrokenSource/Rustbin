import shutil
import subprocess
from functools import partial
from subprocess import CompletedProcess


# Todo: Ensure the venv bin directory is on path or get it directly
def shim(*args: str, proxy: str, **kwargs) -> CompletedProcess:
    return subprocess.run((
        shutil.which(proxy),
        *map(str, args),
    ), **kwargs)

# Export all the shims as python functions
init          = partial(shim, proxy="rustup-init")
cargo         = partial(shim, proxy="cargo")
cargo_clippy  = partial(shim, proxy="cargo-clippy")
cargo_fmt     = partial(shim, proxy="cargo-fmt")
cargo_miri    = partial(shim, proxy="cargo-miri")
clippy_driver = partial(shim, proxy="clippy-driver")
rls           = partial(shim, proxy="rls")
rust_analyzer = partial(shim, proxy="rust-analyzer")
rust_gdb      = partial(shim, proxy="rust-gdb")
rust_gdbgui   = partial(shim, proxy="rust-gdbgui")
rust_lldb     = partial(shim, proxy="rust-lldb")
rustc         = partial(shim, proxy="rustc")
rustdoc       = partial(shim, proxy="rustdoc")
rustfmt       = partial(shim, proxy="rustfmt")
