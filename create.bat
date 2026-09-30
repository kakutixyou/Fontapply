@echo off

REM ルート
mkdir webforge-ai-desktop
cd webforge-ai-desktop

REM Electron
mkdir electron
mkdir electron\ipc
mkdir electron\utils

REM Frontend
mkdir frontend
mkdir frontend\public
mkdir frontend\src
mkdir frontend\src\pages
mkdir frontend\src\components
mkdir frontend\src\components\layout
mkdir frontend\src\components\builder
mkdir frontend\src\components\font
mkdir frontend\src\components\chat
mkdir frontend\src\components\preview
mkdir frontend\src\components\common
mkdir frontend\src\hooks
mkdir frontend\src\store
mkdir frontend\src\api
mkdir frontend\src\styles

REM Python backend
mkdir python_backend
mkdir python_backend\api
mkdir python_backend\services
mkdir python_backend\services\ai_site_builder
mkdir python_backend\services\ai_site_builder\branding
mkdir python_backend\services\font_engine
mkdir python_backend\services\llm_engine
mkdir python_backend\services\llm_engine\providers
mkdir python_backend\services\export_engine
mkdir python_backend\schemas
mkdir python_backend\core

REM Database
mkdir database
mkdir database\repositories
mkdir database\migrations

REM Shared
mkdir shared
mkdir shared\types
mkdir shared\constants

REM Assets
mkdir assets
mkdir assets\base_fonts
mkdir assets\templates
mkdir assets\templates\landing_basic
mkdir assets\templates\portfolio
mkdir assets\templates\corporate
mkdir assets\icons
mkdir assets\sample_sites

REM Scripts
mkdir scripts

echo フォルダ構成作成完了！
pause
