# DAYSIM Configuration Module for CEA External Tools
# This module handles fetching, building, and installing DAYSIM

# Configurable DAYSIM source directory and repository
set(DAYSIM_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/daysim" CACHE PATH "Path to DAYSIM source directory")
set(DAYSIM_GIT_REPOSITORY "https://github.com/reyery/Daysim.git" CACHE STRING "DAYSIM Git repository URL")
set(DAYSIM_GIT_TAG "b4fc6ba3a41e32c8b0d6a41d413aa10f067b6709" CACHE STRING "DAYSIM Git tag/branch to use")

function(configure_daysim)
    message(STATUS "=== Configuring DAYSIM ===")
    
    # Check if DAYSIM source exists locally
    if(EXISTS "${DAYSIM_SOURCE_DIR}/CMakeLists.txt")
        message(STATUS "Found local DAYSIM source at: ${DAYSIM_SOURCE_DIR}")
        add_subdirectory(${DAYSIM_SOURCE_DIR} daysim_build)
        set(DAYSIM_FINAL_SOURCE_DIR "${DAYSIM_SOURCE_DIR}" PARENT_SCOPE)
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
            GIT_SHALLOW TRUE
        )
        
        # Try to fetch and build DAYSIM
        FetchContent_MakeAvailable(daysim_external)
        set(DAYSIM_FINAL_SOURCE_DIR "${daysim_external_SOURCE_DIR}" PARENT_SCOPE)
        message(STATUS "DAYSIM fetched to: ${daysim_external_SOURCE_DIR}")
    endif()
endfunction()

function(install_daysim)
    message(STATUS "=== Setting DAYSIM targets ===")
    
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
                        RUNTIME DESTINATION "${INSTALL_BIN_DIR}"
                        COMPONENT cea_targets)
            else()
                message(WARNING "  - Target ${target} not found")
            endif()
        endforeach()
    else()
        message(FATAL_ERROR "cea_targets target not found in DAYSIM build! Cannot proceed.")
    endif()
endfunction()
