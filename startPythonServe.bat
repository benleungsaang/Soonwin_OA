@echo off
setlocal enabledelayedexpansion
:: 【核心】1. 统一编码为UTF-8，关闭多余输出，同时设置日志文件绝对路径（避免相对路径问题）
chcp 65001 >nul 2>&1
set "LOG_FILE=D:\Soonwin_OA\waitress_service.log"
set "PROJECT_DIR=D:\Soonwin_OA\SoonwinOA_Backend"
set "VENV_ACTIVATE=%PROJECT_DIR%\venv\Scripts\activate.bat"
set "VENV_PYTHON=%PROJECT_DIR%\venv\Scripts\python.exe"
set "WSGI_ENTRY=wsgi:application"
set "HOST=0.0.0.0"
set "PORT=5000"

:: 2. 写入日志分隔符+启动基础信息（解决date/time中文乱码，强制UTF-8输出）
echo. >> !LOG_FILE!
echo ====================================== >> !LOG_FILE!
echo 启动时间：%date% %time:~0,23% >> !LOG_FILE!  :: 截取时间到毫秒，避免超长
echo 系统当前编码：65001(UTF-8) >> !LOG_FILE!
echo 脚本工作目录：%cd% >> !LOG_FILE!
echo 项目目标目录：!PROJECT_DIR! >> !LOG_FILE!
echo 虚拟环境Python路径：!VENV_PYTHON! >> !LOG_FILE!

:: 3. 切换项目目录 - 详细错误判断（记录失败原因+具体错误码）
echo. >> !LOG_FILE!
echo [步骤1] 切换到项目工作目录... >> !LOG_FILE!
cd /d "!PROJECT_DIR!"
if errorlevel 1 (
    echo [错误-步骤1] 切换目录失败！系统错误码：%errorlevel% >> !LOG_FILE!
    echo [错误-步骤1] 请检查目录是否存在：!PROJECT_DIR! >> !LOG_FILE!
    pause >nul
    exit /b %errorlevel%
)
echo [成功-步骤1] 切换后工作目录：%cd% >> !LOG_FILE!

:: 4. 检查虚拟环境核心文件 - 前置校验（避免激活/执行时无提示失败）
echo. >> !LOG_FILE!
echo [步骤2] 检查虚拟环境文件完整性... >> !LOG_FILE!
if not exist "!VENV_ACTIVATE!" (
    echo [错误-步骤2] 虚拟环境激活脚本不存在：!VENV_ACTIVATE! >> !LOG_FILE!
    echo [错误-步骤2] 请检查虚拟环境是否创建成功 >> !LOG_FILE!
    pause >nul
    exit /b 2
)
if not exist "!VENV_PYTHON!" (
    echo [错误-步骤2] 虚拟环境Python可执行文件不存在：!VENV_PYTHON! >> !LOG_FILE!
    echo [错误-步骤2] 虚拟环境可能损坏，请重新创建 >> !LOG_FILE!
    pause >nul
    exit /b 2
)
echo [成功-步骤2] 虚拟环境核心文件校验通过 >> !LOG_FILE!

:: 5. 激活虚拟环境 - 详细日志（输出激活结果+环境变量，错误码+具体原因）
echo. >> !LOG_FILE!
echo [步骤3] 激活Python虚拟环境... >> !LOG_FILE!
call "!VENV_ACTIVATE!" >> !LOG_FILE! 2>&1
if errorlevel 1 (
    echo [错误-步骤3] 虚拟环境激活失败！系统错误码：%errorlevel% >> !LOG_FILE!
    echo [错误-步骤3] 可能原因：虚拟环境损坏、权限不足、脚本被篡改 >> !LOG_FILE!
    pause >nul
    exit /b %errorlevel%
)
echo [成功-步骤3] 虚拟环境激活完成 >> !LOG_FILE!

:: 6. 前置校验Python - 执行版本查询（验证Python可用，记录版本信息）
echo. >> !LOG_FILE!
echo [步骤4] 校验Python可执行性并查询版本... >> !LOG_FILE!
"!VENV_PYTHON!" --version >> !LOG_FILE! 2>&1
if errorlevel 1 (
    echo [错误-步骤4] Python执行失败！系统错误码：%errorlevel% >> !LOG_FILE!
    echo [错误-步骤4] 可能原因：Python文件损坏、权限不足、路径含特殊字符 >> !LOG_FILE!
    pause >nul
    exit /b %errorlevel%
)
echo [成功-步骤4] Python版本校验通过 >> !LOG_FILE!

:: 7. 启动Waitress - 极致详细日志（所有输出/错误都写入，记录启动参数）
echo. >> !LOG_FILE!
echo [步骤5] 开始启动Waitress服务... >> !LOG_FILE!
echo [启动参数] Host:!HOST! ^| Port:!PORT! ^| WSGI入口:!WSGI_ENTRY! >> !LOG_FILE!
echo [启动命令] "!VENV_PYTHON!" -m waitress --host=!HOST! --port=!PORT! !WSGI_ENTRY! >> !LOG_FILE!
:: 核心执行：所有标准输出/错误都写入日志，保留原始报错
"!VENV_PYTHON!" -m waitress --host=!HOST! --port=!PORT! !WSGI_ENTRY! >> !LOG_FILE! 2>&1

:: 8. Waitress退出后 - 详细错误码+原因分析（兜底日志，避免无提示退出）
echo. >> !LOG_FILE!
echo [服务退出] Waitress服务异常/手动退出 >> !LOG_FILE!
echo [退出错误码] %errorlevel% >> !LOG_FILE!
if %errorlevel% equ 0 (
    echo [退出原因] 服务被手动终止（如Ctrl+C），无运行错误 >> !LOG_FILE!
) else if %errorlevel% equ 9009 (
    echo [退出原因] 9009=命令未找到！大概率是Python路径错误/文件不存在 >> !LOG_FILE!
) else if %errorlevel% equ 1 (
    echo [退出原因] 1=通用运行错误！请查看上方日志的Python/Waitress具体报错 >> !LOG_FILE!
) else (
    echo [退出原因] 未知错误码！请结合上方日志的具体报错分析 >> !LOG_FILE!
)
echo ====================================== >> !LOG_FILE!
endlocal
pause >nul