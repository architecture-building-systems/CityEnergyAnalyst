# CRAX Configuration Module for CEA External Tools
# This module handles fetching, building, and installing CRAX

# CRAX configuration options for Python wheel builds
option(CRAX_USE_DYNAMIC_ARROW "Enable dynamic Arrow linking for CRAX (saves space in wheels)" ON)
option(CRAX_USE_AUTOMATED_DEPENDENCIES "Use automated dependency fetching for CRAX" ON)

# Configurable CRAX source directory and repository
set(CRAX_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/crax" CACHE PATH "Path to CRAX source directory")
set(CRAX_GIT_REPOSITORY "https://github.com/wanglittlerain/CityRadiation-Accelerator-CRAX-V1.0.git" CACHE STRING "CRAX Git repository URL")
set(CRAX_GIT_TAG "f54f126eefd1578308c2b73e7096dc9705252303" CACHE STRING "CRAX Git tag/branch to use")

if(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
    # Disable warning C4127 that causes build to fail in Windows
    add_compile_options(
        /wd4127
    )
endif()

function(configure_crax)
    message(STATUS "=== Configuring CRAX ===")

    # Configure CRAX build options before adding to build
    message(STATUS "Configuring CRAX with CEA-specific options:")
    message(STATUS "  Dynamic Arrow: ${CRAX_USE_DYNAMIC_ARROW}")
    message(STATUS "  Automated Dependencies: ${CRAX_USE_AUTOMATED_DEPENDENCIES}")

    # Set CRAX CMake variables to pass our configuration
    set(USE_DYNAMIC_ARROW ${CRAX_USE_DYNAMIC_ARROW} CACHE BOOL "Use dynamic Arrow linking" FORCE)
    set(USE_AUTOMATED_DEPENDENCIES ${CRAX_USE_AUTOMATED_DEPENDENCIES} CACHE BOOL "Use automated dependencies" FORCE)
    
    # Check if CRAX source exists locally
    if(EXISTS "${CRAX_SOURCE_DIR}/CMakeLists.txt")
        message(STATUS "Found local CRAX source at: ${CRAX_SOURCE_DIR}")
        add_subdirectory(${CRAX_SOURCE_DIR} crax_build)
        set(CRAX_FINAL_SOURCE_DIR "${CRAX_SOURCE_DIR}" PARENT_SCOPE)
    else()
        # Fetch CRAX from GitHub using FetchContent
        message(STATUS "Local CRAX source not found, fetching from GitHub...")
        message(STATUS "Repository: ${CRAX_GIT_REPOSITORY}")
        message(STATUS "Tag/Branch: ${CRAX_GIT_TAG}")

        include(FetchContent)
        
        FetchContent_Declare(
            crax_external
            GIT_REPOSITORY ${CRAX_GIT_REPOSITORY}
            GIT_TAG ${CRAX_GIT_TAG}
            GIT_SHALLOW TRUE
        )

        # Try to fetch and build CRAX
        FetchContent_MakeAvailable(crax_external)
        set(CRAX_FINAL_SOURCE_DIR "${crax_external_SOURCE_DIR}" PARENT_SCOPE)
        message(STATUS "CRAX fetched to: ${crax_external_SOURCE_DIR}")
    endif()

    # For Python wheel builds, set the Python executable to match the build environment
    # if(CRAX_USE_DYNAMIC_ARROW)
    #     # Try to find the current Python executable being used for the build
    #     find_package(Python3 COMPONENTS Interpreter QUIET)
    #     if(Python3_FOUND)
    #         set(PYARROW_PYTHON_EXECUTABLE ${Python3_EXECUTABLE} CACHE STRING "Python executable for pyarrow detection" FORCE)
    #         message(STATUS "  Setting PYARROW_PYTHON_EXECUTABLE to: ${Python3_EXECUTABLE}")
    #     endif()
    # endif()
endfunction()

function(install_crax)
    message(STATUS "=== Setting CRAX targets ===")
    
    # Install CRAX executables
    if(TARGET radiation)
        message(STATUS "✓ Found radiation target")
        install(TARGETS radiation
                RUNTIME DESTINATION "${INSTALL_BIN_DIR}"
                COMPONENT crax_targets)
    else()
        message(FATAL_ERROR "radiation target not found")
    endif()

    if(TARGET mesh-generation)
        message(STATUS "✓ Found mesh-generation target") 
        install(TARGETS mesh-generation
                RUNTIME DESTINATION "${INSTALL_BIN_DIR}"
                COMPONENT crax_targets)
    else()
        message(FATAL_ERROR "mesh-generation target not found")
    endif()
endfunction()
