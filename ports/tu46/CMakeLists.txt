# happywars - ReXGlue Recompiled Project
#
# SDK boilerplate lives in generated/rexglue.cmake.

cmake_minimum_required(VERSION 3.25)
project(happywars LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(HAPPYWARS_BUILD_GAME "Compile real translated game (requires successful codegen)" ON)
option(HAPPYWARS_TEST_TRANSLATION "Test an exact generated leaf function with fixture memory" OFF)
include(CTest)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
add_library(offline_store runtime/offline_store.cpp)
target_include_directories(offline_store PUBLIC include)
target_link_libraries(offline_store PUBLIC winsqlite3)
add_library(local_title_storage runtime/local_title_storage.cpp)
target_link_libraries(local_title_storage PUBLIC offline_store)
if(BUILD_TESTING)
    add_executable(local_title_storage_test tests/local_title_storage_test.cpp)
    target_link_libraries(local_title_storage_test PRIVATE local_title_storage)
    add_test(NAME local_title_storage COMMAND local_title_storage_test ${CMAKE_CURRENT_BINARY_DIR}/title-storage-test.sqlite)
    add_executable(store_test tests/store_test.cpp)
    target_link_libraries(store_test PRIVATE offline_store)
    add_test(NAME store_process_restart COMMAND ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/tests/store_process_test.py $<TARGET_FILE:store_test>)
endif()

if(HAPPYWARS_TEST_TRANSLATION)
    find_package(rexglue CONFIG REQUIRED)
    add_executable(local_live_network_test tests/local_live_network_test.cpp runtime/local_live_network.cpp)
    target_link_libraries(local_live_network_test PRIVATE rex::runtime)
    rexglue_apply_target_settings(local_live_network_test)
    add_test(NAME local_live_network COMMAND local_live_network_test)
    add_executable(local_stats_enumerator_test tests/local_stats_enumerator_test.cpp runtime/local_stats_enumerator.cpp)
    target_link_libraries(local_stats_enumerator_test PRIVATE rex::runtime)
    rexglue_apply_target_settings(local_stats_enumerator_test)
    add_test(NAME local_stats_enumerator COMMAND local_stats_enumerator_test ${CMAKE_CURRENT_BINARY_DIR}/stats-enumerator-user)
    add_executable(translated_leaf_test tests/translated_leaf_test.cpp private/tests/translated_leaf.cpp)
    target_include_directories(translated_leaf_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
    target_link_libraries(translated_leaf_test PRIVATE rex::runtime)
    rexglue_apply_target_settings(translated_leaf_test)
    add_test(NAME translated_leaf COMMAND translated_leaf_test)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/private/tests/translated_thunk.cpp")
        add_executable(translated_thunk_test tests/translated_thunk_test.cpp private/tests/translated_thunk.cpp)
        target_include_directories(translated_thunk_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
        target_link_libraries(translated_thunk_test PRIVATE rex::runtime)
        rexglue_apply_target_settings(translated_thunk_test)
        add_test(NAME translated_thunk COMMAND translated_thunk_test)
    endif()
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/private/tests/translated_virtual_adapter.cpp")
        add_executable(translated_virtual_adapter_test tests/translated_virtual_adapter_test.cpp private/tests/translated_virtual_adapter.cpp)
        target_include_directories(translated_virtual_adapter_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
        target_link_libraries(translated_virtual_adapter_test PRIVATE rex::runtime)
        rexglue_apply_target_settings(translated_virtual_adapter_test)
        add_test(NAME translated_virtual_adapter COMMAND translated_virtual_adapter_test)
        if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/private/tests/translated_vcall4.cpp")
            target_sources(translated_virtual_adapter_test PRIVATE private/tests/translated_vcall4.cpp)
            target_compile_definitions(translated_virtual_adapter_test PRIVATE HAPPYWARS_TEST_VCALL4=1)
        endif()
    endif()
    add_executable(offline_network_guard_test tests/offline_network_guard_test.cpp runtime/offline_network_guard.cpp)
    target_link_libraries(offline_network_guard_test PRIVATE rex::runtime)
    rexglue_apply_target_settings(offline_network_guard_test)
    add_test(NAME offline_network_guard COMMAND offline_network_guard_test)
    add_executable(offline_profile_test tests/offline_profile_test.cpp runtime/offline_profile.cpp)
    target_link_libraries(offline_profile_test PRIVATE rex::runtime)
    rexglue_apply_target_settings(offline_profile_test)
    add_test(NAME offline_profile COMMAND offline_profile_test)
    add_executable(offline_auth_test tests/offline_auth_test.cpp runtime/offline_auth.cpp)
    target_link_libraries(offline_auth_test PRIVATE rex::runtime)
    rexglue_apply_target_settings(offline_auth_test)
    add_test(NAME offline_auth COMMAND offline_auth_test)
    add_executable(local_service_directory_test tests/local_service_directory_test.cpp runtime/local_service_directory.cpp)
    target_link_libraries(local_service_directory_test PRIVATE rex::runtime)
    rexglue_apply_target_settings(local_service_directory_test)
    add_test(NAME local_service_directory COMMAND local_service_directory_test)
    add_executable(local_http_test tests/local_http_test.cpp runtime/local_http.cpp runtime/local_http_uri.cpp)
    target_link_libraries(local_http_test PRIVATE rex::runtime local_title_storage)
    rexglue_apply_target_settings(local_http_test)
    add_test(NAME local_http COMMAND local_http_test ${CMAKE_CURRENT_BINARY_DIR}/http-storage-test.sqlite)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/private/tests/translated_stats.cpp")
        add_executable(local_stats_test tests/local_stats_test.cpp runtime/local_stats.cpp private/tests/translated_stats.cpp)
        target_include_directories(local_stats_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
        target_link_libraries(local_stats_test PRIVATE rex::runtime)
        rexglue_apply_target_settings(local_stats_test)
        add_test(NAME local_stats COMMAND local_stats_test)
    endif()
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/private/tests/translated_indexed_dispatch.cpp")
        add_executable(translated_indexed_dispatch_test tests/translated_indexed_dispatch_test.cpp private/tests/translated_indexed_dispatch.cpp)
        target_include_directories(translated_indexed_dispatch_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
        target_link_libraries(translated_indexed_dispatch_test PRIVATE rex::runtime)
        rexglue_apply_target_settings(translated_indexed_dispatch_test)
        add_test(NAME translated_indexed_dispatch COMMAND translated_indexed_dispatch_test)
    endif()
endif()

if(BUILD_TESTING AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/private/tests/native_memory_original.cpp")
    find_package(rexglue CONFIG REQUIRED)
        add_executable(native_memory_test tests/native_memory_test.cpp runtime/native_memory.cpp private/tests/native_memory_original.cpp)
        target_compile_definitions(native_memory_test PRIVATE HAPPYWARS_TU46=1)
        target_include_directories(native_memory_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
        target_link_libraries(native_memory_test PRIVATE rex::runtime)
        rexglue_apply_target_settings(native_memory_test)
        add_test(NAME native_memory COMMAND native_memory_test)
    endif()

if(HAPPYWARS_BUILD_GAME)
include(generated/rexglue.cmake)
set(REXGLUE_CODEGEN_EXECUTABLE "" CACHE FILEPATH "Patched AOT codegen CLI; runtime still uses the pinned SDK")
if(REXGLUE_CODEGEN_EXECUTABLE)
    if(NOT EXISTS "${REXGLUE_CODEGEN_EXECUTABLE}")
        message(FATAL_ERROR "Configured diagnostic codegen CLI does not exist")
    endif()
    # TARGET_FILE in the generated custom command is resolved at generation.
    # Keep this override in project-owned CMake so codegen cannot overwrite it.
    set_property(TARGET rex::rexglue PROPERTY IMPORTED_LOCATION "${REXGLUE_CODEGEN_EXECUTABLE}")
    get_target_property(HAPPYWARS_CODEGEN_CONFIGS rex::rexglue IMPORTED_CONFIGURATIONS)
    foreach(HAPPYWARS_CODEGEN_CONFIG IN LISTS HAPPYWARS_CODEGEN_CONFIGS)
        set_property(TARGET rex::rexglue PROPERTY
            IMPORTED_LOCATION_${HAPPYWARS_CODEGEN_CONFIG} "${REXGLUE_CODEGEN_EXECUTABLE}")
    endforeach()
endif()
# The SDK emits both a sentinel-terminated mapping array and 236k individual
# virtual registration calls. Use that identical ordered array for registration.
list(FILTER REXGLUE_ENTRYPOINT_GENERATED_SOURCES EXCLUDE REGEX "happywars_register[.]cpp$")

# Sources
set(HAPPYWARS_SOURCES
    src/main.cpp
    runtime/offline_network_guard.cpp
    runtime/offline_profile.cpp
    runtime/boot_diagnostics.cpp
    runtime/offline_auth.cpp
    runtime/local_service_directory.cpp
    runtime/local_http.cpp
    runtime/local_http_uri.cpp
    runtime/local_stats.cpp
    runtime/local_stats_enumerator.cpp
    runtime/local_live_network.cpp
    runtime/local_tickets.cpp
    runtime/native_memory.cpp
    runtime/local_premium.cpp
    runtime/performance.cpp
    runtime/fps_overlay.cpp
    runtime/verified_callbacks.cpp
    runtime/function_registration.cpp
)

if(WIN32)
    add_executable(happywars WIN32 ${HAPPYWARS_SOURCES})
else()
    add_executable(happywars ${HAPPYWARS_SOURCES})
endif()

rexglue_setup_target(happywars GPU_PLUGINS xenos)
target_link_libraries(happywars PRIVATE local_title_storage)
add_custom_target(happywars_aot_preflight
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/scripts/validate_translation.py
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/scripts/verify_registration.py
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/scripts/prepare_blr_callbacks.py
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
add_dependencies(happywars_aot_preflight happywars_codegen)
add_dependencies(happywars happywars_aot_preflight)
add_dependencies(happywars_recomp happywars_aot_preflight)
add_custom_target(happywars_diagnostics
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/scripts/diagnose_entries.py
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
add_dependencies(happywars_diagnostics happywars_aot_preflight)
target_include_directories(happywars PRIVATE include)
target_compile_definitions(happywars PRIVATE HAPPYWARS_TU46=1)
set(HAPPYWARS_RECOMP_OPT_LEVEL "0" CACHE STRING "Optimization for translated code; 0 for initial bring-up")
if(NOT HAPPYWARS_RECOMP_OPT_LEVEL MATCHES "^[0-3]$")
    message(FATAL_ERROR "HAPPYWARS_RECOMP_OPT_LEVEL must be 0, 1, 2 or 3")
endif()
target_compile_options(happywars_recomp PRIVATE -O${HAPPYWARS_RECOMP_OPT_LEVEL})
set_target_properties(happywars PROPERTIES OUTPUT_NAME HappyWars)
add_custom_command(TARGET happywars POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/ResetSaves.cmd" "$<TARGET_FILE_DIR:happywars>/ResetSaves.cmd"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/scripts/reset_saves.ps1" "$<TARGET_FILE_DIR:happywars>/reset_saves.ps1")
set(HAPPYWARS_FPS_FONT "${CMAKE_CURRENT_SOURCE_DIR}/private/ui/happywars-fps.ttf")
if(EXISTS "${HAPPYWARS_FPS_FONT}")
set_property(TARGET happywars APPEND PROPERTY LINK_DEPENDS "${HAPPYWARS_FPS_FONT}")
add_custom_command(TARGET happywars POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "$<TARGET_FILE_DIR:happywars>/fonts"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${HAPPYWARS_FPS_FONT}" "$<TARGET_FILE_DIR:happywars>/fonts/happywars-fps.ttf")
endif()
# Storage backend awaits a verified game-specific serialization hook.
endif()
