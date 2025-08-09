# CRAX Configuration Module for CEA External Tools
# This module handles fetching, building, and installing CRAX

# CRAX configuration options for Python wheel builds
option(CRAX_USE_DYNAMIC_ARROW "Enable dynamic Arrow linking for CRAX (saves space in wheels)" ON)
option(CRAX_USE_AUTOMATED_DEPENDENCIES "Use automated dependency fetching for CRAX" ON)

# Configurable CRAX source directory and repository
set(CRAX_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/crax" CACHE PATH "Path to CRAX source directory")
set(CRAX_GIT_REPOSITORY "https://github.com/wanglittlerain/CityRadiation-Accelerator-CRAX-V1.0.git" CACHE STRING "CRAX Git repository URL")
set(CRAX_GIT_TAG "mac-build" CACHE STRING "CRAX Git tag/branch to use")

function(configure_crax)
    message(STATUS "=== Configuring CRAX ===")
    
    # Check if CRAX source exists locally
    if(EXISTS "${CRAX_SOURCE_DIR}/CMakeLists.txt")
        message(STATUS "Found local CRAX source at: ${CRAX_SOURCE_DIR}")
        set(CRAX_FINAL_SOURCE_DIR "${CRAX_SOURCE_DIR}" PARENT_SCOPE)
    else()
        # Fetch CRAX from GitHub using FetchContent
        message(STATUS "Local CRAX source not found, fetching from GitHub...")
        message(STATUS "Repository: ${CRAX_GIT_REPOSITORY}")
        message(STATUS "Tag/Branch: ${CRAX_GIT_TAG}")

        include(FetchContent)
        
        FetchContent_Declare(
            crx_external
            GIT_REPOSITORY ${CRAX_GIT_REPOSITORY}
            GIT_TAG ${CRAX_GIT_TAG}
            GIT_SHALLOW TRUE
        )

        # Try to fetch and build CRAX
        FetchContent_MakeAvailable(crx_external)
        set(CRAX_FINAL_SOURCE_DIR "${crx_external_SOURCE_DIR}" PARENT_SCOPE)
        message(STATUS "CRAX fetched to: ${crx_external_SOURCE_DIR}")
    endif()
endfunction()

function(build_crax CRAX_FINAL_SOURCE_DIR)
    message(STATUS "=== Building CRAX ===")
    message(STATUS "Building CRAX from: ${CRAX_FINAL_SOURCE_DIR}")

    # Configure CRAX build options before adding to build
    message(STATUS "Configuring CRAX with CEA-specific options:")
    message(STATUS "  Dynamic Arrow: ${CRAX_USE_DYNAMIC_ARROW}")
    message(STATUS "  Automated Dependencies: ${CRAX_USE_AUTOMATED_DEPENDENCIES}")

    # Set CRAX CMake variables to pass our configuration
    set(USE_DYNAMIC_ARROW ${CRAX_USE_DYNAMIC_ARROW} CACHE BOOL "Use dynamic Arrow linking" FORCE)
    set(USE_AUTOMATED_DEPENDENCIES ${CRAX_USE_AUTOMATED_DEPENDENCIES} CACHE BOOL "Use automated dependencies" FORCE)
    set(PREFER_PYARROW ON CACHE BOOL "Prefer pyarrow over system Arrow" FORCE)

    # For Python wheel builds, set the Python executable to match the build environment
    if(CRAX_USE_DYNAMIC_ARROW)
        # Try to find the current Python executable being used for the build
        find_package(Python3 COMPONENTS Interpreter QUIET)
        if(Python3_FOUND)
            set(PYARROW_PYTHON_EXECUTABLE ${Python3_EXECUTABLE} CACHE STRING "Python executable for pyarrow detection" FORCE)
            message(STATUS "  Setting PYARROW_PYTHON_EXECUTABLE to: ${Python3_EXECUTABLE}")
        endif()
    endif()

    # Add CRAX to the build
    if(EXISTS "${CRAX_SOURCE_DIR}/CMakeLists.txt")
        # For local CRAX, we need to manually add it to the build
        message(STATUS "Adding local CRAX to build...")
        add_subdirectory(${CRAX_FINAL_SOURCE_DIR} crax_build)
    else()
        # For FetchContent CRAX, it's already added by FetchContent_MakeAvailable
        message(STATUS "CRAX was fetched and added via FetchContent")
        # No need to call add_subdirectory again - FetchContent_MakeAvailable handles it
    endif()
endfunction()

function(install_crax)
    message(STATUS "=== Installing CRAX ===")
    
    # Install CRAX executables
    if(TARGET radiation)
        message(STATUS "✓ Found radiation target")
        install(TARGETS radiation
                RUNTIME DESTINATION "cea/radiation/bin"
                COMPONENT crax_targets)
    else()
        message(WARNING "radiation target not found")
    endif()

    if(TARGET mesh-generation)
        message(STATUS "✓ Found mesh-generation target") 
        install(TARGETS mesh-generation
                RUNTIME DESTINATION "cea/radiation/bin"
                COMPONENT crax_targets)
    else()
        message(WARNING "mesh-generation target not found")
    endif()
endfunction()
