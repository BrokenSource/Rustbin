> [!WARNING]
> 👷‍♂️ Under construction, no releases exists yet 🚧

<div align="center">
  <!-- <img src="https://raw.githubusercontent.com/BrokenSource/Rustman/main/rustman/resources/images/logo.png" width="210"> -->
  <h1>Rustman</h1>
  <p>Fast rustup shims for python</p>
  <a href="https://pypi.org/project/rustman/"><img src="https://img.shields.io/pypi/v/rustman?label=PyPI&color=blue"></a>
  <a href="https://pypi.org/project/rustman/"><img src="https://img.shields.io/pypi/dw/rustman?label=Installs&color=blue"></a>
  <a href="https://github.com/BrokenSource/Rustman/"><img src="https://img.shields.io/github/v/tag/BrokenSource/Rustman?label=GitHub&color=orange"></a>
  <a href="https://github.com/BrokenSource/Rustman/stargazers/"><img src="https://img.shields.io/github/stars/BrokenSource/Rustman?label=Stars&style=flat&color=orange"></a>
  <a href="https://discord.gg/KjqvcYwRHm"><img src="https://img.shields.io/discord/1184696441298485370?label=Discord&style=flat&color=purple"></a>
  <br>
  <br>
</div>

## 🔥 Description

Rustman provides [rustup](https://rustup.rs/) and all of its proxies [(1)](https://github.com/rust-lang/rustup/blob/14f134ee3195639bd18d27ecc4b88c3e5d59559c/src/lib.rs#L20-L51) [(2)](https://github.com/rust-lang/rustup/blob/14f134ee3195639bd18d27ecc4b88c3e5d59559c/src/bin/rustup-init.rs#L94-L124) in a convenient python package.

```python
import rustman

# Install the host's rust toolchain
rustman.rustup("default", "stable")

# Compile a project, run commands
rustman.cargo("--version")
rustman.cargo("run", cwd="my-rust-project")
```

<sup><i><b>Note:</b> This project is not affiliated with the Rust project.</i></sup>

## 📦 Installation

Rustman is available on [PyPI](https://pypi.org/project/rustman/) and can be added to your `pyproject.toml`:

```toml
[project]
dependencies = ["rustman"]
```

(...)

> [!IMPORTANT]
> As mapping system information from [Python Wheels](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/) to a [Rust triple](https://doc.rust-lang.org/nightly/rustc/platform-support.html) is non-trivial, and that the package would balloon in size to include all platforms, primarily **Tier 1** hosts are provided on PyPI.
>
> Attempting to `pip install` on a "unknown" platform will buid an empty Source Distribution (sdist) without binaries - per chicken-and-egg problem needing Rust to build the package.
>
> You can either install [rustup](https://rustup.rs/) externally or set a few environment variables:
>
> ```sh
> $ export RUSTMAN_TRIPLE=powerpc-unknown-linux-gnu
> $ export RUSTMAN_SUFFIX=""
> $ export RUSTMAN_WHEEL="manylinux_2_17_ppc64"
> $ uv build --wheel
> ```
>
> Open issues to tell interest in more platforms!

## 🚀 Speeds

Rustman bundles a small (rust) program to spawn shims faster than `[project.scripts]` ever could:

```sh
# Note: /bin/cargo is effectively a zero-cost symlink
$ RUSTUP_FORCE_ARG0=cargo hyperfine /bin/rustup
  Time (mean ± σ):      30.6 ms ±   0.8 ms    [User: 21.5 ms, System: 8.9 ms]
  Range (min … max):    29.5 ms …  36.0 ms    100 runs

# Shims calling .venv/bin/rustup-init
$ hyperfine .venv/bin/cargo
  Time (mean ± σ):      31.2 ms ±   0.4 ms    [User: 21.7 ms, System: 9.2 ms]
  Range (min … max):    30.5 ms …  32.7 ms    100 runs
```

<sup><b>Note:</b> Full benchmark command was <code>nice -20 taskset -c 2 hyperfine -w 50 -r 100 -N (command)</code></sup>

Less than a millisecond to call a shim, compared to ~80ms for a python script 🚀

## ⚖️ License

Rustman is dual-licensed under the MIT or Apache-2.0 licenses at your option.

