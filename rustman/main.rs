use std::env::args;
use std::env::consts::EXE_EXTENSION;
use std::env::current_exe;
use std::process::Command;
use std::process::exit;

#[cfg(unix)]
use std::os::unix::process::CommandExt;

/// Environment variable takes precedence over argv[0]
const RUSTUP_FORCE_ARG0: &str = "RUSTUP_FORCE_ARG0";

fn main() {
    let executable = current_exe()
        .expect("Failed to get executable path");

    // Universal file name to proxy
    let shim = executable
        .with_extension("")
        .file_name()
        .expect("Failed to get executable name")
        .to_owned();

    // Both are bundled on venv/bin
    let rustup = executable.parent()
        .expect("Failed to get executable parent")
        .join("rustup-init")
        .with_extension(EXE_EXTENSION)
        .to_owned();

    // Windows must create a new process
    #[cfg(windows)] {
        let call = Command::new(rustup)
            .env(RUSTUP_FORCE_ARG0, shim)
            .args(args().skip(1))
            .status();
        if let Err(e) = call {
            eprintln!("Failed to execute shim: {}", e);
            exit(1);
        }
    }

    // Unix-like can replace the current process
    #[cfg(not(windows))] {
        let error = Command::new(rustup)
            .env(RUSTUP_FORCE_ARG0, shim)
            .args(args().skip(1))
            .exec();
        eprintln!("Failed to execute shim: {}", error);
        exit(1);
    }
}
