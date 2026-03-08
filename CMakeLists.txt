cmake_minimum_required(VERSION 3.5)
project(gfnotary VERSION 1.0.0)

find_package(eosio.cdt)

add_contract(gfnotary gfnotary src/gfnotary.cpp)
target_include_directories(gfnotary PUBLIC ${CMAKE_SOURCE_DIR}/include)
