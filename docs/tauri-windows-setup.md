# Tauri Windows Setup

This repository currently contains the blockchain contract. The retail desktop client will be a
separate Tauri application targeting Windows first.

## Current local status

From the current machine state:

- `node` is installed
- `npm` is installed
- `winget` is installed
- `cargo` is missing
- `rustc` is missing
- MSVC Build Tools were not detected in `PATH`
- WebView2 Runtime was not detected by the environment check

## Official Tauri direction

According to the current Tauri v2 docs, the standard project creation flow is:

```bash
npm create tauri-app@latest
```

Or, for manual setup with an existing frontend:

```bash
npm create vite@latest .
npm install -D @tauri-apps/cli@latest
npx tauri init
```

## Windows prerequisites

Install Rust:

```powershell
winget install --id Rustlang.Rustup -e --accept-package-agreements --accept-source-agreements
```

Install Visual Studio Build Tools:

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --accept-package-agreements --accept-source-agreements
```

In the Visual Studio Installer, ensure these are installed:

- `Desktop development with C++`
- MSVC C++ build tools
- Windows 10/11 SDK

Install WebView2 Runtime if it is missing:

```powershell
winget install --id Microsoft.EdgeWebView2Runtime -e --accept-package-agreements --accept-source-agreements
```

## Verify environment

Run:

```powershell
./scripts/check-tauri-windows-env.ps1
```

The environment is ready when all of the following are present:

- `node`
- `npm`
- `rustup`
- `rustc`
- `cargo`
- MSVC Build Tools
- WebView2 Runtime

## Recommended next step

Once prerequisites are green, create the desktop client in a separate folder, for example:

```powershell
mkdir apps\retail-client
cd apps\retail-client
npm create tauri-app@latest .
```

At scaffolding time we should decide the frontend stack explicitly. For a first Windows retail app,
the pragmatic options are:

- Vite + Vanilla TypeScript for a minimal footprint
- Vite + React + TypeScript if we expect richer account flows and state-heavy UI

## Notes

- Tauri uses the system web renderer, so WebView2 matters on Windows.
- Rust must use the MSVC toolchain on Windows for the normal Tauri workflow.
- We have not scaffolded the app yet in this repository; this document only prepares the environment step.
