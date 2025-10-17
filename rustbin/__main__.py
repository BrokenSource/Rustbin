import sys
from functools import partial

import rustbin


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {__package__} <shim> [args...]")
        sys.exit(0)

    # Unpack arguments in a neat way
    python, shim, *args = sys.argv
    shim = shim.replace("-", "_")

    if not (method := getattr(rustbin, shim, None)):
        raise ValueError(f"Shim does not exist: {shim}")

    # Shims are always a partial object,
    # prevent from acessing other stuff
    if not isinstance(method, partial):
        raise ValueError(f"Shim does not exist: {shim}")

    sys.exit(method(*args).returncode)

if __name__ == '__main__':
    main()
