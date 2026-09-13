# Legal Notice & Written Offer

This distribution contains compiled binaries of third-party software libraries, some of which are licensed under the GNU Lesser General Public License (LGPL). These libraries include, but are not limited to:
- FFmpeg
- LibRaw

## License Information
The licenses for all bundled dependencies are included in this distribution within the `share/<package>/copyright` files. Users are encouraged to review these files for the specific terms and conditions applicable to each library.

## Written Offer for Source Code
In accordance with the LGPL, the OpenUTV Team hereby offers to provide the corresponding source code for the LGPL-licensed libraries included in this distribution. This offer is valid for at least three (3) years from the date of your receipt of this binary distribution.

### How to Obtain Source Code
To obtain the exact source code used to build these libraries:
1.  Navigate to the OpenUTV Dependencies repository: [https://github.com/openutv/utv-dependencies](https://github.com/openutv/utv-dependencies)
2.  Follow the build instructions in the `README.md`.
3.  The build system in this repository uses `vcpkg` with a pinned manifest (`vcpkg.json`) and configuration (`vcpkg-configuration.json`). Running the build will automatically and reproducibly fetch the exact upstream source code tarballs used to generate the binaries in this distribution.

Alternatively, you may request the source code directly by opening an issue on the repository mentioned above.
