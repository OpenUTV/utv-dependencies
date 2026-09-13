# OpenUTV Dependencies

This repository holds the automated multi-platform dependency build pipeline for OpenUTV using `vcpkg`.
It generates native installers (`.msi`, `.deb`, `.rpm`) that the primary OpenUTV pipeline consumes.

## Supported Platforms

| Platform | Package Format | Workflow |
|----------|----------------|----------|
| Windows (x64) | MSI (WiX) | `Windows - Build Dependencies` |
| Ubuntu (24.04) | DEB | `Linux (Ubuntu) - Build Dependencies` |
| Rocky Linux (9) | RPM | `Linux (Rocky) - Build Dependencies` |

## Architecture

This project uses a **Manifest-First** approach with `vcpkg`:
- `vcpkg.json`: Centralized list of all 25+ dependencies and their features.
- `vcpkg-configuration.json`: Pins the `vcpkg` registry baseline for reproducible builds.
- `CMakeLists.txt`: Handles cross-platform packaging logic via `CPack`.

## Caching

We leverage the **GitHub Actions Cache** provider for `vcpkg`. Binary packages are cached individually, allowing for extremely fast incremental builds when only a subset of dependencies changes.

## Versioning

This repository uses **Source-Driven Semantic Versioning**.
The version of the generated packages and the GitHub Release tag is defined directly in `CMakeLists.txt`:

```cmake
project(OpenUTVDependencies VERSION 26.1)
```

**⚠️ IMPORTANT NOTE FOR MAINTAINERS:**
Before merging significant dependency updates to the `main` branch, you **MUST increment the version** in `CMakeLists.txt` (e.g., from `26.1` to `26.2`).
If you run a GitHub Action without incrementing the version, it will overwrite (clobber) the existing release assets for that version.

## License & Legal

The build scripts, CMake definitions, and CI pipelines in this repository are licensed under the [MIT License](LICENSE).

This project bundles third-party dependencies under various open-source licenses. Please refer to [LEGAL.md](LEGAL.md) for important information regarding LGPL compliance and our written offer for source code.

