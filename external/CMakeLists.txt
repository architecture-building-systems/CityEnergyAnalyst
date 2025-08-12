cmake_minimum_required(VERSION 3.15)
project(cea_external_tools)

# Set C++ standard if needed
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Suppress common warnings for cleaner build output
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(
        -Wno-unused-variable
        -Wno-unused-parameter
        -Wno-sign-compare
        -Wno-deprecated-declarations
    )
endif()

# Include the separate configuration modules
include(${CMAKE_CURRENT_SOURCE_DIR}/DaysimConfig.cmake)
include(${CMAKE_CURRENT_SOURCE_DIR}/CraxConfig.cmake)

# Build options
option(BUILD_DAYSIM "Build DAYSIM component" ON)
option(BUILD_CRAX "Build CRAX component" ON)

# Configure and build DAYSIM
if(BUILD_DAYSIM)
    message(STATUS "")
    configure_daysim()

    message(STATUS "")
    build_daysim(${DAYSIM_FINAL_SOURCE_DIR})

    message(STATUS "")
    install_daysim()
endif()

# Configure and build CRAX
if(BUILD_CRAX)
    message(STATUS "")
    configure_crax()

    message(STATUS "")
    build_crax(${CRAX_FINAL_SOURCE_DIR})

    message(STATUS "")
    install_crax()
endif()

# ============================================================================
# Custom Build Targets for CEA
# ============================================================================

# Create custom target that builds all CEA-required components
add_custom_target(cea_all)

# A function to add dependencies after targets are defined
function(setup_custom_target_dependencies)
    message(STATUS "=== CEA External Tools Target Summary ===")

    # DAYSIM targets
    if(BUILD_DAYSIM)
        set(CEA_DAYSIM_TARGETS ds_illum epw2wea gen_dc oconv radfiles2daysim rtrace_dc)
        foreach(target ${CEA_DAYSIM_TARGETS})
            if(TARGET ${target})
                add_dependencies(cea_all ${target})
                message(STATUS "  ✓ Added DAYSIM target ${target} to cea_all")
            else()
                message(STATUS "  ⚠ DAYSIM target ${target} not found")
            endif()
        endforeach()
    endif()
    
    # CRAX targets
    if(BUILD_CRAX)
        set(CEA_CRAX_TARGETS radiation mesh-generation)
        foreach(target ${CEA_CRAX_TARGETS})
            if(TARGET ${target})
                add_dependencies(cea_all ${target})
                message(STATUS "  ✓ Added CRAX target ${target} to cea_all")
            else()
                message(STATUS "  ⚠ CRAX target ${target} not found")
            endif()
        endforeach()
    endif()
endfunction()

# Call the function after all subdirectories have been processed
if(BUILD_DAYSIM OR BUILD_CRAX)
    message(STATUS "")
    setup_custom_target_dependencies()
endif()

# Print build information
message(STATUS "")
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
message(STATUS "")
message(STATUS "Usage: cmake --build build --target cea_all")
message(STATUS "===============================================")
