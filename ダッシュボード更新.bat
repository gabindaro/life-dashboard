@echo off
chcp 65001 >nul
echo.
echo ===================================
echo   📊 Life Dashboard 更新ツール
echo ===================================
echo.

set PROJ_DIR=c:\Users\trexa\.gemini\antigravity\playground\ancient-schrodinger
set PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI

echo [1/3] 🔄 自動同期（歩数取得＋読書ノート転記）...
python "%PROJ_DIR%\auto_sync.py"

echo.
echo [2/3] 📊 ダッシュボード生成...
python "%PROJ_DIR%\life_dashboard.py"
if errorlevel 1 (
    echo ❌ エラーが発生しました
    pause
    exit /b 1
)

echo.
echo [3/3] 🚀 GitHubにデプロイ中...
cd /d "%PROJ_DIR%"
git add docs\
git commit -m "update %date% %time:~0,5%" 2>nul
git push origin master
if errorlevel 1 (
    echo ❌ デプロイに失敗しました
    pause
    exit /b 1
)

echo.
echo ✅ 完了！
echo 🌐 https://gabindaro.github.io/life-dashboard/
echo.
echo ブラウザで開きますか？ [何かキーを押すと開きます]
pause >nul
start https://gabindaro.github.io/life-dashboard/
