> [!WARNING]
> Always check the [repository](https://github.com/BrokenSource/Rustbin) for latest readme information.

<div align="center">
  <h1>Rustbin</h1>
  <p>Fast rustup shims for python</p>
  <a href="https://pypi.org/project/rustbin/"><img src="https://img.shields.io/pypi/v/rustbin?label=PyPI&color=blue"></a>
  <a href="https://pypi.org/project/rustbin/"><img src="https://img.shields.io/pypi/dw/rustbin?label=Installs&color=blue"></a>
  <a href="https://github.com/BrokenSource/Rustbin/stargazers/"><img src="https://img.shields.io/github/stars/BrokenSource/Rustbin?label=Stars&style=flat&color=orange"></a>
  <a href="https://discord.gg/KjqvcYwRHm"><img src="https://img.shields.io/discord/1184696441298485370?label=Discord&style=flat&color=purple"></a>
  <br>
  <br>
</div>

## 🔥 Description

Rustbin provides [rustup](https://rustup.rs/) and all of its proxies `cargo, rustc..` [(1)](https://github.com/rust-lang/rustup/blob/14f134ee3195639bd18d27ecc4b88c3e5d59559c/src/lib.rs#L20-L51) [(2)](https://github.com/rust-lang/rustup/blob/14f134ee3195639bd18d27ecc4b88c3e5d59559c/src/bin/rustup-init.rs#L94-L124)  in a convenient python package.

```python
# After installation
$ tree .venv
.venv
├── bin
│   ├── cargo
│   ├── rustc
│   └── rustup-init
(...)
```

✅ Also check out [Rustman](https://github.com/BrokenSource/Rustman), for python methods, easy cross compilation, management and automation!

<sup><i><b>Note:</b> This is a community repackaging effort with no affiliation to the Rust project.</i></sup>

## 📦 Installation

Rustbin is available on [PyPI](https://pypi.org/project/rustbin/) and can be added to your `pyproject.toml` or `pip install`ed directly:

```toml
[project]
dependencies = ["rustbin"]
```

Versioning of the [package](https://pypi.org/project/rustbin/#history) will follow:

- Same as [rustup](https://github.com/rust-lang/rustup/tags), without rushes to match all upstream releases (at least a month stable).
- Broken releases might be deleted and re-uploaded as 'post' within a week, if needed.
- New platforms might be added post-release at any time, and with no version bump.
- Ancient versions _might_ be removed to save space, in case a [size grant](https://docs.pypi.org/project-management/storage-limits/) is not given.

> [!IMPORTANT]
>
> As mapping system information from [Python/Wheels](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/) to a [Rust Triple](https://doc.rust-lang.org/nightly/rustc/platform-support.html) is non-trivial, and that the package needs rust to build from source, attempting to `pip install` on _"unknown"_ platforms without [prebuilt wheels](https://pypi.org/project/rustbin/#files) on pypi will make an empty one from source without rustup or shims.
>
> **Your best path** is to install [rustup](https://rustup.rs/) externally in such cases, this package essentially becomes a no-op.

Open issues to tell interest in platforms that are actually used, so the package doesn't balloon in size!

## 🚀 Speeds

Rustbin bundles a small [(rust)](../rustbin/main.rs) program to spawn shims faster than `[project.scripts]` ever could:

> ✅ Less than a millisecond overhead, compared to ~105ms for a python script

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

## ⚖️ License

Rustbin is dual-licensed under the MIT or Apache-2.0 license, at your option.
