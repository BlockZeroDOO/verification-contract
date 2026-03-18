cmake_minimum_required(VERSION 3.5)
project(verification_contracts VERSION 1.0.0)

find_package(eosio.cdt)

add_contract(verification verification src/verification.cpp)
target_include_directories(verification PUBLIC ${CMAKE_SOURCE_DIR}/include)

add_contract(managementel managementel src/managementel.cpp)
target_include_directories(managementel PUBLIC ${CMAKE_SOURCE_DIR}/include)

add_contract(dfs dfs src/dfs.cpp)
target_include_directories(dfs PUBLIC ${CMAKE_SOURCE_DIR}/include)
