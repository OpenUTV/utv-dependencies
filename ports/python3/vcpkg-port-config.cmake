include_guard(GLOBAL)
set(PYTHON3_VERSION "3.14.5")
set(PYTHON3_VERSION_MAJOR "3")
set(PYTHON3_VERSION_MINOR "14")
set(PYTHON3_INCLUDE "include/python3.14")
set(PYTHON3_HAS_EXTENSIONS "1")

if(VCPKG_TARGET_IS_WINDOWS)
    set(PYTHON3_SITE "tools/python3/Lib/site-packages")
else()
    set(PYTHON3_SITE "lib/python3.14/site-packages")
endif()

include("${CURRENT_HOST_INSTALLED_DIR}/share/vcpkg-get-python/vcpkg-port-config.cmake")
