cmake_minimum_required(VERSION 3.15)
project(cea_external_tools)

# Set C++ standard if needed
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Platform-specific output directory for CEA's expected structure
if(WIN32)
    set(CEA_PLATFORM_DIR "win32")
elseif(APPLE)
    set(CEA_PLATFORM_DIR "darwin")
else()
    set(CEA_PLATFORM_DIR "linux")
endif()

# Include the separate configuration modules
include(${CMAKE_CURRENT_SOURCE_DIR}/DaysimConfig.cmake)
include(${CMAKE_CURRENT_SOURCE_DIR}/CraxConfig.cmake)

# Build options
option(BUILD_DAYSIM "Build DAYSIM component" ON)
option(BUILD_CRAX "Build CRAX component" ON)

# Configure and build DAYSIM
if(BUILD_DAYSIM)
    configure_daysim()
    build_daysim(${DAYSIM_FINAL_SOURCE_DIR})
    install_daysim(${CEA_PLATFORM_DIR})
endif()

# Configure and build CRAX
if(BUILD_CRAX)
    configure_crax()
    build_crax(${CRAX_FINAL_SOURCE_DIR})
    install_crax(${CEA_PLATFORM_DIR})
endif()

# Print build information
message(STATUS "=== CEA External Tools Configuration Summary ===")
message(STATUS "  Platform: ${CEA_PLATFORM_DIR}")
message(STATUS "  Build DAYSIM: ${BUILD_DAYSIM}")
message(STATUS "  Build CRAX: ${BUILD_CRAX}")
if(BUILD_DAYSIM)
    message(STATUS "  DAYSIM source: ${DAYSIM_SOURCE_DIR}")
endif()
if(BUILD_CRAX)
    message(STATUS "  CRAX source: ${CRAX_SOURCE_DIR}")
endif()
message(STATUS "  Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "===============================================")
