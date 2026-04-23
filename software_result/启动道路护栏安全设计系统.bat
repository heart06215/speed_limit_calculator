@echo off
chcp 65001 >nul
title 道路护栏安全设计系统 v4.0
echo ========================================
echo   道路护栏安全设计系统 v4.0
echo   基于气候数据的护栏选型与碰撞模拟
echo ========================================
echo.
echo   正在启动服务，请稍候...
echo   服务就绪后将自动打开浏览器
echo   关闭此窗口即可停止服务
echo.

cd /d "%~dp0"

:: 后台启动打包后的 exe（Flask 内嵌服务器）
start /B "" "%~dp0道路护栏安全设计系统.exe"

:: 轮询等待 Flask 就绪（最多 15 秒，每隔 1 秒检测一次）
set /a tries=0
:waitloop
set /a tries+=1
if %tries% gtr 15 (
    echo.
    echo   [警告] 服务未在 15 秒内就绪，直接尝试打开浏览器...
    goto openbrowser
)
:: 用 PowerShell 检测 5000 端口是否有响应
powershell -nologo -noprofile -command "try { $null=Invoke-WebRequest 'http://localhost:5000' -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel%==0 goto openbrowser
timeout /t 1 /nobreak >nul
echo   等待服务就绪... (%tries%/15)
goto waitloop

:openbrowser
echo.
echo   服务已就绪，正在打开浏览器...
start "" http://localhost:5000

echo.
echo   [提示] 关闭此窗口将停止后端服务。
pause >nul
taskkill /F /IM "道路护栏安全设计系统.exe" >nul 2>&1
