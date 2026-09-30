import os
folders = ["webforge-ai-desktop/electron/ipc","webforge-ai-desktop/electron/utils",
"webforge-ai-desktop/frontend/public",
"webforge-ai-desktop/frontend/src/pages",
"webforge-ai-desktop/frontend/src/components/layout",
"webforge-ai-desktop/frontend/src/components/builder",
"webforge-ai-desktop/frontend/src/components/font",
"webforge-ai-desktop/frontend/src/components/chat",
"webforge-ai-desktop/frontend/src/components/preview",
"webforge-ai-desktop/frontend/src/components/common",
"webforge-ai-desktop/frontend/src/hooks",
"webforge-ai-desktop/frontend/src/store",
"webforge-ai-desktop/frontend/src/api",
"webforge-ai-desktop/frontend/src/styles",

"webforge-ai-desktop/python_backend/api",
"webforge-ai-desktop/python_backend/services/ai_site_builder/branding",
"webforge-ai-desktop/python_backend/services/font_engine",
"webforge-ai-desktop/python_backend/services/llm_engine/providers",
"webforge-ai-desktop/python_backend/services/export_engine",
"webforge-ai-desktop/python_backend/schemas",
"webforge-ai-desktop/python_backend/core",

"webforge-ai-desktop/database/repositories",
"webforge-ai-desktop/database/migrations",

"webforge-ai-desktop/shared/types",
"webforge-ai-desktop/shared/constants",

"webforge-ai-desktop/assets/base_fonts",
"webforge-ai-desktop/assets/templates/landing_basic",
"webforge-ai-desktop/assets/templates/portfolio",
"webforge-ai-desktop/assets/templates/corporate",
"webforge-ai-desktop/assets/icons",
"webforge-ai-desktop/assets/sample_sites",

"webforge-ai-desktop/scripts",
]
for folder in folders:os.makedirs(folder, exist_ok=True)
print("フォルダ構成を作成しました！")