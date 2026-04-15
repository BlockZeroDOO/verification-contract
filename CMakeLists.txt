cmake_minimum_required(VERSION 3.5)
project(verification_contracts VERSION 1.0.0)

find_package(eosio.cdt)

add_contract(verifent verifent src/verification.cpp)
target_include_directories(verifent PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_compile_definitions(verifent PRIVATE VERIFICATION_ENTERPRISE_BUILD)
target_sources(
    verifent
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src/verification_enterprise.cpp
        ${CMAKE_SOURCE_DIR}/src/verification_core.cpp
)

add_contract(verifretail verifretail src/verification_retail_entry.cpp)
target_include_directories(verifretail PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_compile_definitions(verifretail PRIVATE VERIFICATION_RETAIL_BUILD)
target_sources(
    verifretail
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src/verification_retail.cpp
        ${CMAKE_SOURCE_DIR}/src/verification_core.cpp
)
