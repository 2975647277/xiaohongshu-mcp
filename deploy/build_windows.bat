@echo off
REM 打包成 Windows .exe，双击直接运行，不需要安装 Python
echo 📦 开始打包 Windows 应用...

set INSTALL_DIR=%USERPROFILE%\xiaohongshu-mcp
cd /d %INSTALL_DIR%

python -m pip install pyinstaller flask anthropic Pillow requests -q

python -m PyInstaller ^
  --name "小红书AI发布助手" ^
  --onefile ^
  --windowed ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --hidden-import flask ^
  --hidden-import anthropic ^
  --hidden-import PIL ^
  --hidden-import requests ^
  app.py

echo.
echo ✅ 打包完成！
echo    应用位置: %INSTALL_DIR%\dist\小红书AI发布助手.exe
echo    双击即可运行，无需安装 Python
explorer "%INSTALL_DIR%\dist\"
pause
