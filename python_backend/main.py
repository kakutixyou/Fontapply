from __future__ import annotations

import asyncio
import os
import sqlite3
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# python_backend/main.py を直接実行した場合の import パス調整
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# === 今回の大動脈で使うルーター ===
from python_backend.api.routes_font_generator import init_glyph_overrides_table, router as font_generator_router
from python_backend.api.routes_projects import init_projects_table, router as projects_router

# === 古い/壊れているルーターは一時的に無効化（エラー回避のため） ===
# from python_backend.api.routes_font_export import router as font_export_router
# from python_backend.api.routes_font_analytics import cache_manager, router as font_analytics_router
# from python_backend.api.routes_font_import import router as font_import_router
# from python_backend.core.font_cache import CacheCleanupScheduler

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "font_studio.db"
MIGRATIONS_DIR = BASE_DIR / "database" / "migrations"

def _run_migrations() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            file_name TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        already_applied = cur.execute(
            "SELECT 1 FROM schema_migrations WHERE file_name = ?",
            (sql_file.name,),
        ).fetchone()
        if already_applied:
            continue
        cur.executescript(sql_file.read_text(encoding="utf-8"))
        cur.execute(
            "INSERT INTO schema_migrations (file_name) VALUES (?)",
            (sql_file.name,),
        )
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 起動時の処理 (startup) ---
    _run_migrations()
    init_projects_table()
    init_glyph_overrides_table()
    
    # ※古いキャッシュクリーンアップ処理は一旦停止しています
    yield 

app = FastAPI(title="WebForge AI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "null",
        *[
            origin.strip()
            for origin in os.environ.get("FONT_API_CORS_ORIGINS", "").split(",")
            if origin.strip()
        ],
    ],
    allow_origin_regex=r"^app://.*$|^file://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 有効化するルーティング ===
app.include_router(projects_router, prefix="/projects")
app.include_router(font_generator_router, prefix="/api")

# === 無効化中のルーティング ===
# app.include_router(font_export_router, prefix="/api")
# app.include_router(font_import_router, prefix="/api")
# app.include_router(font_analytics_router, prefix="/api")

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.environ.get("FONT_API_HOST", "127.0.0.1"),
        port=int(os.environ.get("FONT_API_PORT", "8000")),
    )