cmake_minimum_required(VERSION 3.5)
project(verification_contracts VERSION 1.0.0)

find_package(eosio.cdt)

add_contract(verif verif src/verification.cpp)
target_include_directories(verif PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_compile_definitions(verif PRIVATE VERIFICATION_ENTERPRISE_BUILD)
target_sources(
    verif
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

add_contract(verifbill verifbill src/verification_billing_entry.cpp)
target_include_directories(verifbill PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_sources(
    verifbill
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src/verification_billing.cpp
)

add_contract(verifretpay verifretpay src/verification_retail_payment_entry.cpp)
target_include_directories(verifretpay PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_sources(
    verifretpay
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src/verification_retail_payment.cpp
)
