#!/bin/bash

# ルート
mkdir webforge-ai-desktop
cd webforge-ai-desktop

# Electron
mkdir -p electron/ipc
mkdir -p electron/utils

# Frontend
mkdir -p frontend/public
mkdir -p frontend/src/pages
mkdir -p frontend/src/components/layout
mkdir -p frontend/src/components/builder
mkdir -p frontend/src/components/font
mkdir -p frontend/src/components/chat
mkdir -p frontend/src/components/preview
mkdir -p frontend/src/components/common
mkdir -p frontend/src/hooks
mkdir -p frontend/src/store
mkdir -p frontend/src/api
mkdir -p frontend/src/styles

# Python backend
mkdir -p python_backend/api
mkdir -p python_backend/services/ai_site_builder/branding
mkdir -p python_backend/services/font_engine
mkdir -p python_backend/services/llm_engine/providers
mkdir -p python_backend/services/export_engine
mkdir -p python_backend/schemas
mkdir -p python_backend/core

# Database
mkdir -p database/repositories
mkdir -p database/migrations

# Shared
mkdir -p shared/types
mkdir -p shared/constants

# Assets
mkdir -p assets/base_fonts
mkdir -p assets/templates/landing_basic
mkdir -p assets/templates/portfolio
mkdir -p assets/templates/corporate
mkdir -p assets/icons
mkdir -p assets/sample_sites

# Scripts
mkdir -p scripts

echo "フォルダ構成作成完了！"