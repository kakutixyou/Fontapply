# webforge-ai-desktop/python_backend/api/routes_projects.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import sqlite3
import json
from pathlib import Path
from datetime import datetime

router = APIRouter()

# データベースのパス設定 (main.pyと同じ階層を参照)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "database" / "font_studio.db"

# ==========================================
# 1. Pydantic スキーマ定義 (データの型チェック)
# ==========================================
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = ""
    project_type: str = "font"  # "font" または "site" などを想定
    settings: dict = {}

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 2. データベース接続・初期化
# ==========================================
def get_db_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # カラム名でアクセスできるようにする
    return conn

def init_projects_table():
    """テーブルが存在しない場合は自動作成する"""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            project_type TEXT,
            settings TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ルーター読み込み時にテーブルを準備
init_projects_table()

# ==========================================
# 3. エンドポイント (CRUD操作)
# ==========================================

@router.get("/", response_model=List[ProjectResponse])
async def list_projects():
    """プロジェクト一覧の取得 (List)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()

    projects = []
    for row in rows:
        projects.append(ProjectResponse(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            project_type=row["project_type"],
            settings=json.loads(row["settings"]) if row["settings"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        ))
    return projects

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """新規プロジェクトの作成 (Create)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    settings_json = json.dumps(project.settings)
    cursor.execute("""
        INSERT INTO projects (name, description, project_type, settings)
        VALUES (?, ?, ?, ?)
    """, (project.name, project.description, project.project_type, settings_json))
    
    project_id = cursor.lastrowid
    if project_id is None:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail="Failed to create project")
    
    conn.commit()
    conn.close()
    
    return await get_project(int(project_id))

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    """特定のプロジェクトの取得 (Read)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        project_type=row["project_type"],
        settings=json.loads(row["settings"]) if row["settings"] else {},
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project: ProjectUpdate):
    """プロジェクトの更新 (Update)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 存在確認
    cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")

    settings_json = json.dumps(project.settings)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        UPDATE projects
        SET name = ?, description = ?, project_type = ?, settings = ?, updated_at = ?
        WHERE id = ?
    """, (project.name, project.description, project.project_type, settings_json, now, project_id))
    
    conn.commit()
    conn.close()
    
    return await get_project(project_id)

@router.delete("/{project_id}")
async def delete_project(project_id: int):
    """プロジェクトの削除 (Delete)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")

    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Project deleted successfully"}