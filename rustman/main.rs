use std::env::args;
use std::env::consts::EXE_SUFFIX;
use std::env::current_exe;
use std::env::set_var;
use std::process::Command;
use std::process::exit;

#[cfg(unix)]
use std::os::unix::process::CommandExt;

fn main() {

    // Both are bundled on venv/bin
    let rustup = current_exe()
        .expect("Failed to get executable path")
        .parent()
        .expect("Failed to get executable parent")
        .join("rustup-init")
        .with_extension(EXE_SUFFIX);

    // Warn: Compile-time required variable
    // Environment takes precedence over process name
    unsafe {set_var("RUSTUP_FORCE_ARG0", env!("SHIM"))}

    // Windows must create a new process
    if cfg!(windows) {
        let error = Command::new(rustup)
            .args(args().skip(1))
            .status();
        if let Err(e) = error {
            eprintln!("Failed to execute rustup: {}", e);
            exit(1);
        }

    // Unix-like replaces the current process
    } else {
        let error = Command::new(rustup)
            .args(args().skip(1))
            .exec();
        eprintln!("Failed to execute rustup: {}", error);
        exit(1);
    }
}
