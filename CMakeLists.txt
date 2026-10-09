# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

# Les tests de Core **hors du moteur** (LOT-1014).
#
# Le jeu se construit par UnrealBuildTool (`JustAnotherRpgGame.uproject`) ; cette construction-ci
# ne sert qu'à compiler la bibliothèque des règles seule, avec GoogleTest, comme l'ancien dépôt le
# faisait. Les mêmes sources sont compilées deux fois : par le moteur, dans le module du jeu, et
# ici, sans lui. Une règle que le moteur impose à Core s'écrit dans Core et vaut pour les deux.
#
#   cmake --preset ninja && cmake --build --preset ninja && ctest --preset ninja

cmake_minimum_required(VERSION 3.21)

# Le numéro de version a une seule source, `VERSION.txt` : le module du jeu
# (`JustAnotherRpgGame.Build.cs`) et `scripts/build.ps1` lisent le même fichier.
file(STRINGS ${CMAKE_CURRENT_SOURCE_DIR}/VERSION.txt JADG_VERSION_TEXT LIMIT_COUNT 1)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/VERSION.txt)

project(JustAnotherRpgGameCore
    VERSION ${JADG_VERSION_TEXT}
    DESCRIPTION "Les règles d20, le monde, les quêtes : la bibliothèque Core du jeu, testée sans le moteur"
    LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(ENABLE_WARNINGS_AS_ERRORS "Traiter les avertissements comme des erreurs" ON)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# --- Exceptions : Core signale ses erreurs de lecture par exception (nlohmann) ---
# CMake ne pose plus /EHsc de lui-même avec ce toolchain ; sans lui, <chrono> émet C4530 et /WX
# en fait une erreur sur chaque unité.
if(MSVC)
    add_compile_options(/EHsc)
endif()

# --- Avertissements (nos cibles seulement) ---
add_library(project_warnings INTERFACE)
if(MSVC)
    target_compile_options(project_warnings INTERFACE
        /W4 /permissive- /external:anglebrackets /external:W0)
    if(ENABLE_WARNINGS_AS_ERRORS)
        target_compile_options(project_warnings INTERFACE /WX)
    endif()
else()
    target_compile_options(project_warnings INTERFACE -Wall -Wextra -Wpedantic)
    if(ENABLE_WARNINGS_AS_ERRORS)
        target_compile_options(project_warnings INTERFACE -Werror)
    endif()
endif()

# --- nlohmann/json : l'en-tête unique vendu dans Source/ThirdParty, le même que lit le moteur ---
add_library(nlohmann_json INTERFACE)
add_library(nlohmann_json::nlohmann_json ALIAS nlohmann_json)
target_include_directories(nlohmann_json SYSTEM INTERFACE
    ${PROJECT_SOURCE_DIR}/Source/ThirdParty/nlohmann/include)

# --- Core : tous les .cpp de Source/JustAnotherRpgGame/Core, comme le moteur les prend ---
file(GLOB_RECURSE CORE_SOURCES CONFIGURE_DEPENDS
    ${PROJECT_SOURCE_DIR}/Source/JustAnotherRpgGame/Core/*.cpp)
add_library(Core STATIC ${CORE_SOURCES})
# Racine d'inclusion : "Core/<Module>/<Fichier>.h", jamais un nom seul.
target_include_directories(Core PUBLIC ${PROJECT_SOURCE_DIR}/Source/JustAnotherRpgGame)
target_compile_definitions(Core PRIVATE JADG_VERSION="${PROJECT_VERSION}")
target_link_libraries(Core PUBLIC nlohmann_json::nlohmann_json)
target_link_libraries(Core PRIVATE project_warnings)

# --- GoogleTest ---
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.15.2
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

# --- Les tests unitaires de Core ---
enable_testing()
include(GoogleTest)

file(GLOB_RECURSE CORE_TESTS CONFIGURE_DEPENDS
    ${PROJECT_SOURCE_DIR}/Source/Test/Unit/Core/*.cpp)

add_executable(CoreTests ${CORE_TESTS})
# Les tests incluent leur support en "Test/Support/<Fichier>.h" : la racine est Source/.
target_include_directories(CoreTests PRIVATE ${PROJECT_SOURCE_DIR}/Source)
target_link_libraries(CoreTests PRIVATE Core GTest::gtest_main project_warnings)
set(_elements ${PROJECT_SOURCE_DIR}/Source/Elements)
set(_fixtures ${PROJECT_SOURCE_DIR}/Source/Test/Fixtures)
target_compile_definitions(CoreTests PRIVATE
    JADG_TEST_FIXTURES_DIR="${_fixtures}"
    JADG_TEST_DATA_DIR="${_fixtures}/GameData"
    JADG_MESH_FIXTURE_DIR="${_fixtures}/Meshes"
    JADG_CHARACTER_FIXTURE_DIR="${_fixtures}/Characters"
    JADG_ELEMENTS_DIR="${_elements}"
    JADG_LEVELS_DIR="${_elements}/Levels"
    JADG_RPG_SCHEMA_DIR="${_elements}/Rpg/schema"
    JADG_RPG_RULES_DIR="${_elements}/Rpg/rules"
    JADG_RPG_CREATURES_DIR="${_elements}/Rpg/creatures"
    JADG_RPG_DIR="${_elements}/Rpg"
    JADG_WORLD_DIR="${_elements}/World"
    JADG_ASSETS_DIR="${_elements}/Assets"
    JADG_SOURCE_DIR="${PROJECT_SOURCE_DIR}/Source/JustAnotherRpgGame"
    JADG_FR_LANG_PATH="${_elements}/Localization/fr.lang"
    JADG_EN_LANG_PATH="${_elements}/Localization/en.lang")

gtest_discover_tests(CoreTests
    PROPERTIES LABELS unitaire
    DISCOVERY_TIMEOUT 60)
