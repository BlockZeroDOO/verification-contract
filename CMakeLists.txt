cmake_minimum_required(VERSION 3.5)
project(verification_contracts VERSION 1.0.0)

find_package(eosio.cdt)

add_contract(verification verification src/verification.cpp)
target_include_directories(verification PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_compile_definitions(verification PRIVATE VERIFICATION_ENTERPRISE_BUILD)
target_sources(
    verification
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src/verification_enterprise.cpp
        ${CMAKE_SOURCE_DIR}/src/verification_core.cpp
)

add_contract(verification_retail verifretail src/verification_retail_entry.cpp)
target_include_directories(verification_retail PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_compile_definitions(verification_retail PRIVATE VERIFICATION_RETAIL_BUILD)
target_sources(
    verification_retail
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src/verification_retail.cpp
        ${CMAKE_SOURCE_DIR}/src/verification_core.cpp
)
