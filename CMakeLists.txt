cmake_minimum_required(VERSION 3.15)
project(OpenUTVDependencies VERSION 26.3)

# The vcpkg export or install tree is expected to be in 'exported_deps'
# On Windows, it's typically 'exported_deps/utv-deps-windows-x64'
# On Linux, we'll use a similar structure
if(WIN32)
    set(DEPS_SUBDIR "utv-deps-windows-x64")
elseif(APPLE)
    set(DEPS_SUBDIR "utv-deps-osx-arm64")
else()
    # Assuming Linux x64 for now
    set(DEPS_SUBDIR "utv-deps-linux-x64")
endif()

install(DIRECTORY ${CMAKE_SOURCE_DIR}/exported_deps/${DEPS_SUBDIR}/ DESTINATION . COMPONENT deps)
install(FILES ${CMAKE_SOURCE_DIR}/LEGAL.md DESTINATION . COMPONENT deps)

set(CPACK_PACKAGE_NAME "OpenUTVDeps")
set(CPACK_PACKAGE_VENDOR "OpenUTV")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "OpenUTV Dependencies Bundle")

if(WIN32)
    set(CPACK_GENERATOR "WIX")
    set(CPACK_WIX_UPGRADE_GUID "D2305530-58FF-4054-94E6-37D35E445EFA")
    
    # Define a custom WIX source file to inject the Environment component
    file(WRITE ${CMAKE_BINARY_DIR}/extra.wxs "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Wix xmlns=\"http://schemas.microsoft.com/wix/2006/wi\">
    <Fragment>
        <DirectoryRef Id=\"INSTALL_ROOT\">
            <Component Id=\"EnvVarComponent\" Guid=\"B4E63C47-D611-4770-9856-F1439F68B610\">
                <Environment Id=\"UpdateOpenUTVDepsRoot\" Action=\"set\" Name=\"OPENUTV_DEPS_ROOT\" Value=\"[INSTALL_ROOT]\" System=\"yes\" Permanent=\"no\" />
                <Environment Id=\"UpdatePath\" Action=\"set\" Name=\"PATH\" Value=\"[INSTALL_ROOT]bin\" Part=\"last\" System=\"yes\" Permanent=\"no\" />
            </Component>
        </DirectoryRef>
    </Fragment>
    <Fragment>
        <FeatureRef Id=\"ProductFeature\">
            <ComponentRef Id=\"EnvVarComponent\" />
        </FeatureRef>
    </Fragment>
</Wix>
")
    set(CPACK_WIX_EXTRA_SOURCES "${CMAKE_BINARY_DIR}/extra.wxs")
elseif(UNIX AND NOT APPLE)
    set(CPACK_SET_DESTDIR ON)
    set(CPACK_PACKAGING_INSTALL_PREFIX "/usr/local/openutv-deps")

    # Check if we are on Debian/Ubuntu or RHEL/Rocky
    if(EXISTS "/etc/debian_version")
        set(CPACK_GENERATOR "DEB")
        set(CPACK_DEBIAN_PACKAGE_MAINTAINER "OpenUTV Team")
        set(CPACK_DEBIAN_PACKAGE_SECTION "devel")
        set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
        set(CPACK_DEBIAN_PACKAGE_ARCHITECTURE "amd64")
    else()
        set(CPACK_GENERATOR "RPM")
        set(CPACK_RPM_PACKAGE_LICENSE "Multiple")
        set(CPACK_RPM_PACKAGE_GROUP "Development/Libraries")
        set(CPACK_RPM_PACKAGE_ARCHITECTURE "x86_64")
        set(CPACK_RPM_EXCLUDE_FROM_AUTO_FILELIST_ADDITION
            "/etc"
            "/etc/ld.so.conf.d"
            "/etc/profile.d"
            "/usr/local"
        )
    endif()

    # Create a ld.so.conf.d file to make libraries globally discoverable
    file(WRITE ${CMAKE_BINARY_DIR}/openutv-deps.conf "${CPACK_PACKAGING_INSTALL_PREFIX}/lib\n")
    install(FILES ${CMAKE_BINARY_DIR}/openutv-deps.conf DESTINATION /etc/ld.so.conf.d COMPONENT deps)

    # Create environment profile to append bin to PATH and set OPENUTV_DEPS_ROOT (zero-config)
    file(WRITE ${CMAKE_BINARY_DIR}/openutv-deps.sh
        "export OPENUTV_DEPS_ROOT=\"${CPACK_PACKAGING_INSTALL_PREFIX}\"\n"
        "case \":\$PATH:\" in\n"
        "  *:${CPACK_PACKAGING_INSTALL_PREFIX}/bin:*);;\n"
        "  *) export PATH=\"\$PATH:${CPACK_PACKAGING_INSTALL_PREFIX}/bin\";;\n"
        "esac\n"
    )
    install(FILES ${CMAKE_BINARY_DIR}/openutv-deps.sh DESTINATION /etc/profile.d COMPONENT deps)

    # Run ldconfig after installation/removal
    set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA "${CMAKE_CURRENT_SOURCE_DIR}/scripts/postinst;${CMAKE_CURRENT_SOURCE_DIR}/scripts/postrm")
    set(CPACK_RPM_POST_INSTALL_SCRIPT_FILE "${CMAKE_CURRENT_SOURCE_DIR}/scripts/postinst")
    set(CPACK_RPM_POST_UNINSTALL_SCRIPT_FILE "${CMAKE_CURRENT_SOURCE_DIR}/scripts/postrm")
endif()

include(CPack)
