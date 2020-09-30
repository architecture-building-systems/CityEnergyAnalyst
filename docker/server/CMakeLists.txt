cmake_minimum_required(VERSION 3.0)
cmake_policy(SET CMP0020 NEW)
cmake_policy(SET CMP0048 NEW)
if(NOT ${CMAKE_VERSION} VERSION_LESS "3.1")
  cmake_policy(SET CMP0054 NEW)
endif()

project(daysim VERSION 5.2.0)

add_definitions(-DDAYSIM)

set(PROJECT_VERSION_TWEAK "Unknown" CACHE STRING "Commit Hash")
find_package(Git)
if(GIT_FOUND)
  execute_process(COMMAND "${GIT_EXECUTABLE}" "rev-parse" "--short=10" "HEAD"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    TIMEOUT 10
    RESULT_VARIABLE RESULT
    OUTPUT_VARIABLE GIT_VERSION
    ERROR_QUIET
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
  if(${RESULT} EQUAL 0 AND NOT "${GIT_VERSION}" EQUAL "${PROJECT_VERSION_TWEAK}")
    set(PROJECT_VERSION_TWEAK ${GIT_VERSION} CACHE STRING "Commit Hash" FORCE)
  endif()
endif()

enable_testing()
include(CTest)

option(BUILD_SHARED_LIBS "Build Daysim using shared libraries?" OFF)
option(BUILD_HEADLESS "Build Daysim without any GUI components?" OFF)
option(BUILD_PABOPTO_UTILS "Build PABOpto Utilities?" OFF)
option(BUILD_LIBTIFF "Build libtiff?" OFF)

if(NOT WIN32)
  set(CPACK_INCLUDE_TOPLEVEL_DIRECTORY 1)
  install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/doc/man/" DESTINATION man)
  set(qt_plugin_term "PLUGIN")
endif()

if(WIN32)
  set(CPACK_NSIS_MODIFY_PATH 1)
  set(qt_plugin_term "LIBRARY")

  # Set RAYPATH on install
  set(CPACK_NSIS_EXTRA_INSTALL_COMMANDS
    "WriteRegExpandStr HKLM \\\"SYSTEM\\\\CurrentControlSet\\\\Control\\\\Session Manager\\\\Environment\\\" RAYPATH '\\\$INSTDIR\\\\lib\\\;.'"
  )

  # Unset RAYPATH on uninstall
  set(CPACK_NSIS_EXTRA_UNINSTALL_COMMANDS
    "DeleteRegValue HKLM \\\"SYSTEM\\\\CurrentControlSet\\\\Control\\\\Session Manager\\\\Environment\\\" RAYPATH"
  )
endif()

if(UNIX)
  set(CPACK_PACKAGING_INSTALL_PREFIX "/usr/local/daysim")
  add_definitions(-Dlinux -D_FILE_OFFSET_BITS=64 -DNOSTEREO)
else()
  set(CPACK_PACKAGING_INSTALL_PREFIX "/")
endif()

set(CPACK_PACKAGE_FILE_NAME "${CMAKE_PROJECT_NAME}-${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_TWEAK}-${CMAKE_SYSTEM_NAME}")

if(APPLE)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c11 -std=c++11 -stdlib=libc++")
  add_definitions(-DBSD -DNOSTEREO -Dfreebsd)
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -mmacosx-version-min=10.7")
endif()

if(BUILD_LIBTIFF)
  include(ExternalProject)
  set(LIBTIFF_URL http://download.osgeo.org/libtiff/tiff-4.0.9.tar.gz)
  set(LIBTIFF_MD5 54BAD211279CC93EB4FCA31BA9BFDC79)
  if(WIN32)
    ExternalProject_Add(libtiff
      URL ${LIBTIFF_URL}
      URL_MD5 ${LIBTIFF_MD5}
      CMAKE_GENERATOR "NMake Makefiles"
      CMAKE_ARGS
        "-DBUILD_SHARED_LIBS=OFF"
        "-DCMAKE_BUILD_TYPE=Release"
        "-Dzlib=OFF"
        "../libtiff"
      INSTALL_COMMAND ""
    )
    set(TIFF_LIBRARY ${CMAKE_BINARY_DIR}/libtiff-prefix/src/libtiff-build/libtiff/tiff.lib)
  else()
    ExternalProject_Add(libtiff
      URL ${LIBTIFF_URL}
      URL_MD5 ${LIBTIFF_MD5}
      CMAKE_ARGS
        "-DBUILD_SHARED_LIBS=OFF"
        "-DCMAKE_BUILD_TYPE=Release"
        "-Dzlib=OFF"
        "../libtiff"
      INSTALL_COMMAND ""
    )
    set(TIFF_LIBRARY ${CMAKE_BINARY_DIR}/libtiff-prefix/src/libtiff-build/libtiff/libtiff.a)
  endif()
  set(TIFF_INCLUDE_DIR ${CMAKE_BINARY_DIR}/libtiff/src/libtiff/libtiff)
endif()

set(CPACK_PACKAGE_VERSION_MAJOR ${PROJECT_VERSION_MAJOR})
set(CPACK_PACKAGE_VERSION_MINOR ${PROJECT_VERSION_MINOR})
set(CPACK_PACKAGE_INSTALL_DIRECTORY "Daysim")
set(CPACK_RESOURCE_FILE_WELCOME "${daysim_SOURCE_DIR}/Welcome.txt")
set(CPACK_RESOURCE_FILE_README "${daysim_SOURCE_DIR}/README.txt")
set(CPACK_RESOURCE_FILE_LICENSE "${daysim_SOURCE_DIR}/License.txt")

if(APPLE)
  set(CPACK_GENERATOR "PackageMaker")
elseif(UNIX)
  set(CPACK_GENERATOR "TGZ")
endif()

include(CPack)

if(NOT BUILD_HEADLESS)
  find_package(Qt5Widgets)
  get_target_property(QT_LIBRARY_DIR Qt5::Core LOCATION)
  get_filename_component(QT_LIBRARY_DIR ${QT_LIBRARY_DIR} PATH)
  get_filename_component(QT_LIBRARY_DIR "${QT_LIBRARY_DIR}/.." ABSOLUTE)
  find_package(X11)
  if(APPLE)
     include_directories(${X11_INCLUDE_DIR})
  endif()
endif()

set(EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)

if(MSVC)
  add_definitions(/MP)
endif()
if(WIN32 AND "${CMAKE_C_COMPILER_ID}" MATCHES "^(Intel)$")
  set(_INTEL_WINDOWS 1)
endif()
if(MSVC OR _INTEL_WINDOWS)
  add_definitions(-D_CRT_SECURE_NO_DEPRECATE -D_CRT_NONSTDC_NO_DEPRECATE)
endif()
if(WIN32)
  add_definitions(-DEZXML_NOMMAP -Dfseeko=fseek -Dstrcasecmp=_stricmp)
endif()

add_subdirectory("src")

set(test_dir "${CMAKE_CURRENT_SOURCE_DIR}/test/test data")

add_subdirectory(resources)

install(DIRECTORY "${CMAKE_BINARY_DIR}/lib/"
  DESTINATION "lib"
)

include(InstallRequiredSystemLibraries)
add_subdirectory(InstallRules)
