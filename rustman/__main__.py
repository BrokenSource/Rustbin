import sys
from functools import partial

import rustman


def main():
    if len(sys.argv) < 2:
        print("Usage: rustman <shim> [args...]")
        sys.exit(0)

    # Unpack arguments neat way
    python, shim, *args = sys.argv

    if not (method := getattr(rustman, shim, None)):
        raise ValueError(f"Shim does not exist: {shim}")

    # Shims are always a partial object
    if not isinstance(method, partial):
        raise ValueError(f"Shim does not exist: {shim}")

    sys.exit(method(*args).returncode)

if __name__ == '__main__':
    main()
