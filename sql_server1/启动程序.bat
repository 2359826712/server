@echo off
chcp 65001 >nul
echo ====================================
echo SQL Server 启动工具
echo ====================================
echo.

:: 检查端口9091是否被占用
echo 检查端口9091的占用情况...
netstat -ano | findstr :9091 >nul
if %errorlevel% == 0 (
    echo 端口9091已被占用，正在查找占用进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9091') do set PID=%%a
    echo 占用端口的进程ID: %PID%
    
    :: 检查是否是本程序占用的端口
    for /f "tokens=1" %%b in ('tasklist /fi "PID eq %PID%" ^| findstr "sql_server_windows.exe"') do set PROC_NAME=%%b
    if "%PROC_NAME%" == "sql_server_windows.exe" (
        echo 发现本程序已在运行（PID: %PID%），正在终止...
        taskkill /f /pid %PID%
        if %errorlevel% == 0 (
            echo 成功终止进程！
        ) else (
            echo 终止进程失败，请手动终止占用端口的程序。
        )
    ) else (
        echo 端口被其他程序占用，请手动处理。
    )
    echo.
)

:: 启动程序
echo 启动SQL Server程序...
echo.
echo ====================================
echo 程序输出信息：
echo ====================================

:: 启动程序并保持窗口打开
sql_server_windows.exe

:: 如果程序意外退出，显示错误信息
if %errorlevel% neq 0 (
    echo.
    echo ====================================
    echo 程序启动失败！错误代码: %errorlevel%
    echo 请检查以上输出信息查找原因。
    echo ====================================
    pause
)
