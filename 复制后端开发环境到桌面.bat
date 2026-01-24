@echo off
chcp 65001 > nul 2>&1
title OA后端 - 迁移文件同步脚本
cls

:: 配置区
set "DEV_DIR=E:\Soonwin_OA\soonwin-os-Python-Server"
set "DEPLOY_DIR=%USERPROFILE%\Desktop\OA后端迁移包"
set "COPY_FILES=*.py config.py requirements.txt extensions.py soonwin_oa.db"
set "EXCLUDE_FILES=venv __pycache__ *.pyc *.log *.tmp .gitignore .git"

:: 用户确认生成最新依赖
set /p confirm_req=是否从当前环境生成最新的requirements.txt？(y/n): 
if /i "!confirm_req!"=="y" (
    echo 正在生成包含Python版本信息的requirements.txt...
    if exist "%DEV_DIR%\venv\Scripts\python.exe" (
        echo # Python Version: > "%DEV_DIR%\requirements.txt"
        "%DEV_DIR%\venv\Scripts\python.exe" --version >> "%DEV_DIR%\requirements.txt"
        echo. >> "%DEV_DIR%\requirements.txt"
        "%DEV_DIR%\venv\Scripts\python.exe" -m pip freeze >> "%DEV_DIR%\requirements.txt"
    ) else (
        echo # Python Version: > "%DEV_DIR%\requirements.txt"
        python --version >> "%DEV_DIR%\requirements.txt"
        echo. >> "%DEV_DIR%\requirements.txt"
        python -m pip freeze >> "%DEV_DIR%\requirements.txt"
    )
    echo 最新的requirements.txt生成成功。
) else (
    echo 使用现有的requirements.txt文件。
)

:: 前置检查
echo ==================================================
echo                开始同步迁移文件...
echo ==================================================
echo 开发环境目录: %DEV_DIR%
echo 迁移目标目录: %DEPLOY_DIR%
echo ==================================================

:: 检查开发目录是否存在
if not exist "%DEV_DIR%" (
    echo [ERROR] 开发环境目录不存在！
    echo 请检查路径是否正确。
    pause
    exit /b 1
)

:: 创建迁移目录
if not exist "%DEPLOY_DIR%" (
    echo [INFO] 迁移目录不存在，自动创建: %DEPLOY_DIR%
    md "%DEPLOY_DIR%"
)

:: 清理迁移目录冗余文件
echo [CLEAN] 清理迁移目录冗余文件...
for /d /r "%DEPLOY_DIR%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q "%DEPLOY_DIR%\*.pyc" > nul 2>&1
del /s /q "%DEPLOY_DIR%\*.log" > nul 2>&1
del /s /q "%DEPLOY_DIR%\*.tmp" > nul 2>&1
echo [CLEAN] 冗余文件清理完成

:: 复制核心文件
echo [COPY] 开始复制核心文件...
cd /d "%DEV_DIR%"

for %%f in (%COPY_FILES%) do (
    if exist "%%f" (
        echo [COPY] 复制 %%f
        copy /y "%%f" "%DEPLOY_DIR%\" > nul 2>&1
    ) else (
        echo [SKIP] 文件不存在，跳过 %%f
    )
)

:: 复制根目录中的特定文件
echo [COPY] 复制特定文件...
cd /d "E:\Soonwin_OA"

if exist "Soonwin OA 系统 - Windows 生产环境部署指南.md" (
    echo [COPY] 复制 Soonwin OA 系统 - Windows 生产环境部署指南.md
    copy /y "Soonwin OA 系统 - Windows 生产环境部署指南.md" "%DEPLOY_DIR%\" > nul 2>&1
)

if exist "启动服务器_生产环境_迁移版.bat" (
    echo [COPY] 复制 启动服务器_生产环境_迁移版.bat
    copy /y "启动服务器_生产环境_迁移版.bat" "%DEPLOY_DIR%\" > nul 2>&1
)

cd /d "%DEV_DIR%"

:: 复制必需的子文件夹
if exist "app" (
    echo [COPY] 复制app文件夹
    xcopy /e /y "app" "%DEPLOY_DIR%\app\" > nul 2>&1
)

if exist "migrations" (
    echo [COPY] 复制migrations文件夹
    xcopy /e /y "migrations" "%DEPLOY_DIR%\migrations\" > nul 2>&1
)

if exist "assets" (
    echo [COPY] 复制assets文件夹结构
    xcopy /e /y /t "assets" "%DEPLOY_DIR%\assets\" > nul 2>&1
)

if exist "instance" (
    echo [COPY] 复制instance文件夹
    xcopy /e /y "instance" "%DEPLOY_DIR%\instance\" > nul 2>&1
)

if exist "other" (
    echo [COPY] 复制other文件夹
    xcopy /e /y "other" "%DEPLOY_DIR%\other\" > nul 2>&1
)

if exist "alembic.ini" (
    echo [COPY] 复制alembic.ini
    copy /y "alembic.ini" "%DEPLOY_DIR%\" > nul 2>&1
)

:: 复制前端静态文件
echo [COPY] 复制前端静态文件...
set "FRONTEND_DIR=E:\Soonwin_OA\soonwin-oa-VUE-FrontEnd"
if exist "%FRONTEND_DIR%\dist" (
    echo [COPY] 复制前端dist文件夹
    xcopy /e /y "%FRONTEND_DIR%\dist" "%DEPLOY_DIR%\static\" > nul 2>&1
) else (
    echo [WARN] 前端dist目录不存在
)

:: 复制依赖清单
echo [COPY] 复制依赖清单...
if exist "%DEV_DIR%\requirements.txt" (
    copy /y "%DEV_DIR%\requirements.txt" "%DEPLOY_DIR%\" > nul 2>&1
)
echo [DONE] 依赖清单已复制

:: 完成提示
echo.
echo ==================================================
echo [SUCCESS] 迁移文件同步完成！
echo [PATH] 迁移包路径: %DEPLOY_DIR%
echo [TIP] 后续更新代码后，重新运行本脚本即可同步覆盖！
echo ==================================================
pause
exit /b 0