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

# Configurable DAYSIM source directory and repository
set(DAYSIM_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/daysim" CACHE PATH "Path to DAYSIM source directory")
set(DAYSIM_GIT_REPOSITORY "https://github.com/reyery/Daysim.git" CACHE STRING "DAYSIM Git repository URL")
set(DAYSIM_GIT_TAG "release" CACHE STRING "DAYSIM Git tag/branch to use")

# Check if DAYSIM source exists locally
if(EXISTS "${DAYSIM_SOURCE_DIR}/CMakeLists.txt")
    message(STATUS "Found local DAYSIM source at: ${DAYSIM_SOURCE_DIR}")
    set(DAYSIM_FINAL_SOURCE_DIR "${DAYSIM_SOURCE_DIR}")
else()
    # Fetch DAYSIM from GitHub using FetchContent
    message(STATUS "Local DAYSIM source not found, fetching from GitHub...")
    message(STATUS "Repository: ${DAYSIM_GIT_REPOSITORY}")
    message(STATUS "Tag/Branch: ${DAYSIM_GIT_TAG}")
    
    include(FetchContent)
    
    FetchContent_Declare(
        daysim_external
        GIT_REPOSITORY ${DAYSIM_GIT_REPOSITORY}
        GIT_TAG ${DAYSIM_GIT_TAG}
    )
    
    # Try to fetch and build DAYSIM
    FetchContent_MakeAvailable(daysim_external)
    set(DAYSIM_FINAL_SOURCE_DIR "${daysim_external_SOURCE_DIR}")
    message(STATUS "DAYSIM fetched to: ${DAYSIM_FINAL_SOURCE_DIR}")
endif()

# DAYSIM is now added to the build (either locally or via FetchContent)
message(STATUS "Building DAYSIM from: ${DAYSIM_FINAL_SOURCE_DIR}")

# Add DAYSIM to the build
if(EXISTS "${DAYSIM_SOURCE_DIR}/CMakeLists.txt")
    # For local DAYSIM, we need to manually add it to the build
    message(STATUS "Adding local DAYSIM to build...")
    add_subdirectory(${DAYSIM_FINAL_SOURCE_DIR} daysim_build)
else()
    # For FetchContent DAYSIM, it's already added by FetchContent_MakeAvailable
    message(STATUS "DAYSIM was fetched and added via FetchContent")
    # No need to call add_subdirectory again - FetchContent_MakeAvailable handles it
endif()
    
    # Verify cea_targets target exists (this is what we want to build)
    if(TARGET cea_targets)
        message(STATUS "✓ Found cea_targets custom target")

        # Get the dependencies of cea_targets to see what executables it builds
        get_target_property(CEA_TARGET_DEPS cea_targets MANUALLY_ADDED_DEPENDENCIES)
        if(CEA_TARGET_DEPS)
            message(STATUS "  - cea_targets depends on: ${CEA_TARGET_DEPS}")
        endif()
        
        # PROBLEM: DAYSIM doesn't use the cea_targets COMPONENT in its install() commands
        # We need to install the CEA-specific targets manually
        # FIXME: Update DAYSIM CMakeLists.txt to use COMPONENT for CEA targets

        # Install the specific executables that cea_targets depends on
        set(CEA_EXECUTABLES ds_illum epw2wea gen_dc oconv radfiles2daysim rtrace_dc)
        foreach(target ${CEA_EXECUTABLES})
            if(TARGET ${target})
                message(STATUS "  - Installing ${target}")
                install(TARGETS ${target}
                        RUNTIME DESTINATION "cea/resources/radiation/bin/${CEA_PLATFORM_DIR}"
                        COMPONENT cea_targets)
            else()
                message(WARNING "  - Target ${target} not found")
            endif()
        endforeach()
    else()
        message(FATAL_ERROR "cea_targets target not found in DAYSIM build! Cannot proceed.")
    endif()

# Print build information
message(STATUS "CEA External Tools Configuration:")
message(STATUS "  Platform: ${CEA_PLATFORM_DIR}")
message(STATUS "  DAYSIM source: ${DAYSIM_SOURCE_DIR}")
message(STATUS "  Install prefix: ${CMAKE_INSTALL_PREFIX}")
