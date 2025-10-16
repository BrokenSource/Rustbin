### 👷‍♂️ Under Construction 🚧

Working ideas:
- [x] Small rust project for spawning shims faster
    - [ ] Integrate it with the build script
- [ ] Manual map from `rust-triple` to `wheel-tag`
- [ ] Callable shims methods in python package

<hr>

## 📦 Installation

(...)

As matching available system information from Python to a Rust platform triple is non-trivial, rustman provides manually selected, pre-built wheels for common platforms.

Attempting to `pip install` on a "unknown" platform will need to manually pass a configuration via environment:

```
$ export RUSTUP_TRIPLE=powerpc-unknown-linux-gnu
$ export RUSTUP_SUFFIX=""
$ export RUSTUP_WHEEL="manylinux_2_17_ppc64"
$ pip install rustman
```

(...)

## Speeds

Rustman bundles a small (rust) program to spawn shims faster than `[project.scripts]` ever could:

```
# With RUSTUP_FORCE_ARG0=cargo, /bin/cargo is often a symlink
❯ nice -20 taskset -c 2 hyperfine -w 50 -r 100 -N /bin/rustup
  Time (mean ± σ):      30.6 ms ±   0.8 ms    [User: 21.5 ms, System: 8.9 ms]
  Range (min … max):    29.5 ms …  36.0 ms    100 runs

# Shims calling .venv/bin/rustup-init
❯ nice -20 taskset -c 2 hyperfine -w 50 -r 100 -N .venv/bin/cargo
  Time (mean ± σ):      31.2 ms ±   0.4 ms    [User: 21.7 ms, System: 9.2 ms]
  Range (min … max):    30.5 ms …  32.7 ms    100 runs
```

Less than a millisecond to call a shim, compared to ~80ms for a python script 🚀

## License

Rustman is dual-licensed under the MIT and Apache-2.0 licenses.
