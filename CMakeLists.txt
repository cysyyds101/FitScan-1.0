# FitScan 项目 CMake 配置文件
# 项目编译系统的核心依赖文件

cmake_minimum_required(VERSION 3.10)

project(FitScan)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# 包含目录
include_directories(main/src)

# 查找依赖
find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

# 核心源代码文件
set(SOURCE_FILES
    main/src/core/reference_detector.py
    main/src/core/pose_estimator.py
    main/src/core/geometry_calculator.py
    main/src/core/size_recommender.py
    main/src/utils/video_capture.py
    main/src/utils/visualizer.py
    main/src/config/config.py
    main/main.py
    main/geometry_calculator.py
    main/size_recommender.py
    main/visualizer.py
)

# 测试文件
set(TEST_FILES
    main/tests/test_environment.py
    main/tests/test_reference_detector.py
)

# 资源文件
set(RESOURCE_FILES
    videos/test_a4.jpg
    videos/test_result.jpg
)

# 编译配置文件
set(CONFIG_FILES
    sdkconfig/requirements.txt
    sdkconfig/requirements_optimized.txt
    sdkconfig/run.bat
    sdkconfig/run.sh
    sdkconfig/OPTIMIZATION_GUIDE.md
)

# 文档文件
set(DOC_FILES
    README.md
    pytest_display.py
)

# 安装规则
install(FILES ${SOURCE_FILES} DESTINATION src)
install(FILES ${TEST_FILES} DESTINATION tests)
install(FILES ${RESOURCE_FILES} DESTINATION videos)
install(FILES ${CONFIG_FILES} DESTINATION sdkconfig)
install(FILES ${DOC_FILES} DESTINATION .)

# 构建目标
add_custom_target(
    run
    COMMAND python main/main.py
    DEPENDS ${SOURCE_FILES}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

add_custom_target(
    test
    COMMAND python pytest_display.py
    DEPENDS ${SOURCE_FILES} ${TEST_FILES}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

# 显示项目信息
message(STATUS "FitScan 项目配置完成")
message(STATUS "源代码目录: ${CMAKE_CURRENT_SOURCE_DIR}/main")
message(STATUS "配置文件目录: ${CMAKE_CURRENT_SOURCE_DIR}/sdkconfig")
message(STATUS "资源文件目录: ${CMAKE_CURRENT_SOURCE_DIR}/videos")
