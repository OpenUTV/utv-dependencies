vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO python/cpython
    REF v3.14.5
    SHA512 387075c9dcfb8f2945ab9857947ff743361e6a7ed3d2064858752a2ddd5ad54d1060d08cc67857915523511cc3399a42628c4ed93328d1698adbab5b51fe4bc2
    HEAD_REF main
)

if(VCPKG_TARGET_IS_WINDOWS)
    # Windows build using PCbuild/build.bat
    
    file(TO_NATIVE_PATH "${CURRENT_INSTALLED_DIR}" NATIVE_INSTALLED_DIR)
    
    # Help build.bat find dependencies from vcpkg
    set(ENV{INCLUDE} "$ENV{INCLUDE};${CURRENT_INSTALLED_DIR}/include")
    set(ENV{LIB} "$ENV{LIB};${CURRENT_INSTALLED_DIR}/lib")
    
    # CPython's build.bat expects some things in a specific layout
    # We can try to satisfy it by setting some specific variables if known, 
    # but INCLUDE/LIB is a good start.
    
    # Ensure Git is on PATH
    vcpkg_find_acquire_program(GIT)
    get_filename_component(GIT_DIR "${GIT}" DIRECTORY)
    vcpkg_add_to_path("${GIT_DIR}")

    vcpkg_execute_required_process(
        COMMAND "${SOURCE_PATH}/PCbuild/build.bat" 
                "-p" "x64" 
                "-c" "Release"
                "-e"
                "--no-tkinter"
        WORKING_DIRECTORY "${SOURCE_PATH}/PCbuild"
        LOGNAME "build-${TARGET_TRIPLET}-release"
    )
    
    # Manual installation of binaries to the vcpkg layout
    file(INSTALL "${SOURCE_PATH}/PCbuild/amd64/python.exe" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3")
    file(INSTALL "${SOURCE_PATH}/PCbuild/amd64/python.exe" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3" RENAME "python3.exe")
    file(INSTALL "${SOURCE_PATH}/PCbuild/amd64/pythonw.exe" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3")
    file(INSTALL "${SOURCE_PATH}/PCbuild/amd64/python314.dll" DESTINATION "${CURRENT_PACKAGES_DIR}/bin")
    file(INSTALL "${SOURCE_PATH}/PCbuild/amd64/python314.dll" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3")
    file(INSTALL "${SOURCE_PATH}/PCbuild/amd64/python314.lib" DESTINATION "${CURRENT_PACKAGES_DIR}/lib")
    file(INSTALL "${SOURCE_PATH}/PCbuild/amd64/python314.lib" DESTINATION "${CURRENT_PACKAGES_DIR}/lib" RENAME "python3.lib")

    # Make tools/python3 a complete Python environment for Windows FindPython3
    file(INSTALL "${SOURCE_PATH}/PCbuild/amd64/python314.lib" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3/libs")
    file(INSTALL "${SOURCE_PATH}/PCbuild/amd64/python314.lib" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3/libs" RENAME "python3.lib")
    file(COPY "${SOURCE_PATH}/Include/" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3/include")
    file(INSTALL "${SOURCE_PATH}/PC/pyconfig.h" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3/include")

    # Install Headers to standard vcpkg include layout
    file(COPY "${SOURCE_PATH}/Include/" DESTINATION "${CURRENT_PACKAGES_DIR}/include/python3.14")
    file(INSTALL "${SOURCE_PATH}/PC/pyconfig.h" DESTINATION "${CURRENT_PACKAGES_DIR}/include/python3.14")
    
    # Generic include path for ports that expect 'include/python3'
    file(MAKE_DIRECTORY "${CURRENT_PACKAGES_DIR}/include/python3")
    file(COPY "${CURRENT_PACKAGES_DIR}/include/python3.14/" DESTINATION "${CURRENT_PACKAGES_DIR}/include/python3")
    
    # Install the standard library
    file(INSTALL "${SOURCE_PATH}/Lib" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3")
    file(INSTALL "${SOURCE_PATH}/Lib" DESTINATION "${CURRENT_PACKAGES_DIR}/share/python3")

else()
    # Linux/Unix build using ./configure
    vcpkg_configure_make(
        SOURCE_PATH "${SOURCE_PATH}"
        OPTIONS
            --enable-shared
            --with-system-ffi
            --with-system-expat
            --without-ensurepip
            --enable-optimizations
    )

    vcpkg_install_make()
    vcpkg_fixup_pkgconfig()

    # Provide tools/python3 layout for consumers and FindPython3
    file(MAKE_DIRECTORY "${CURRENT_PACKAGES_DIR}/tools/python3")
    file(MAKE_DIRECTORY "${CURRENT_PACKAGES_DIR}/tools/python3/bin")
    file(GLOB PYTHON_EXECS "${CURRENT_PACKAGES_DIR}/bin/python3*")
    foreach(PY_EXEC ${PYTHON_EXECS})
        if(NOT IS_DIRECTORY "${PY_EXEC}")
            file(COPY "${PY_EXEC}" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3")
            file(COPY "${PY_EXEC}" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/python3/bin")
        endif()
    endforeach()
endif()

file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
