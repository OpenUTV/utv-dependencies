# Project Instructions & Architecture

This file provides context on the build architecture and non-standard dependency configurations in this repository.

## Python 3.14.5 Custom Build
The project utilizes an experimental/custom build of **Python 3.14.5** (CPython). This is managed via a vcpkg overlay port located in `ports/python3/`.

### Why a Custom Port?
- Standard vcpkg ports typically lag behind the latest Python releases (often capped at 3.12).
- The project requires specific Python 3.14 features or testing against the latest C-API.
- The `ports/python3` overlay builds from source using the `PCbuild/build.bat` on Windows to ensure maximum compatibility with the MSVC toolchain used for other dependencies.

## OpenImageIO Overlay (`ports/openimageio/`)
A custom overlay for **OpenImageIO (v3.1.12.0)** was created to resolve Python discovery issues on Windows.

### The Problem
Standard vcpkg discovery logic (`vcpkg_get_vcpkg_installed_python`) often fails to correctly identify Python 3.14 paths, leading to failures in the `pybind11` feature build (Python bindings).

### The Solution
The overlay port's `portfile.cmake` contains explicit overrides for Windows:
- It bypasses automatic discovery.
- It hard-codes paths to the vcpkg-installed tools and libraries:
    - `Python3_EXECUTABLE` -> `tools/python3/python.exe`
    - `Python3_INCLUDE_DIR` -> `include/python3.14`
    - `Python3_LIBRARY` -> `lib/python314.lib`

## pybind11 & Python 3.14
- **Version Requirement**: Python 3.14 support requires **pybind11 v3.0.0 or later**.
- **Configuration**: An explicit override for `pybind11` version `3.0.1` is maintained in `vcpkg.json` to ensure compatibility across all platforms.

## Dependency Management (vcpkg)
- **Manifest Mode**: The project strictly uses `vcpkg.json` in manifest mode.
- **Overlay Registry**: Local overrides in `ports/` are prioritized via `vcpkg-configuration.json`.
- **Baseline**: The project is pinned to vcpkg commit `759f4cca281639f2a0541741c80372012c92477e`. Any updates to the baseline should be tested against the custom overlays in `ports/`.

## CI/CD Workflow
- **Windows**: Build utilizes `windows-2025-vs2026` runners.
- **Caching**: Extensive binary caching is used. If changing overlay ports, the `vcpkg.json` hash will change, triggering a cache rebuild.
