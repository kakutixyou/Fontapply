import asyncio
from typing import Dict, Set
from datetime import datetime
import uuid

class UserSession:
    """ユーザーのセッション情報"""
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.project_id: str = None
        self.cursor_position: Dict[str, int] = {"x": 0, "y": 0}
        self.selected_glyph: str = None
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()


class CollaborationConnectionManager:
    """WebSocket コネクション・セッション管理"""
    
    def __init__(self):
        # {project_id: {session_id: UserSession}}
        self.active_sessions: Dict[str, Dict[str, UserSession]] = {}
        # {session_id: room_id} - 復帰用
        self.session_to_project: Dict[str, str] = {}
    
    def create_session(self, user_id: str, project_id: str) -> UserSession:
        """新規セッション作成"""
        session_id = str(uuid.uuid4())
        session = UserSession(user_id, session_id)
        session.project_id = project_id
        
        if project_id not in self.active_sessions:
            self.active_sessions[project_id] = {}
        
        self.active_sessions[project_id][session_id] = session
        self.session_to_project[session_id] = project_id
        
        return session
    
    def close_session(self, session_id: str):
        """セッション終了"""
        if session_id in self.session_to_project:
            project_id = self.session_to_project[session_id]
            if project_id in self.active_sessions:
                self.active_sessions[project_id].pop(session_id, None)
            self.session_to_project.pop(session_id, None)
    
    def get_active_users(self, project_id: str) -> list:
        """プロジェクト内のアクティブユーザー一覧"""
        if project_id not in self.active_sessions:
            return []
        
        return [
            {
                "user_id": session.user_id,
                "session_id": session.session_id,
                "cursor_position": session.cursor_position,
                "selected_glyph": session.selected_glyph,
            }
            for session in self.active_sessions[project_id].values()
        ]
    
    def update_presence(self, session_id: str, cursor_x: int, cursor_y: int, glyph_id: str = None):
        """ユーザープレゼンス更新"""
        for project_sessions in self.active_sessions.values():
            if session_id in project_sessions:
                session = project_sessions[session_id]
                session.cursor_position = {"x": cursor_x, "y": cursor_y}
                session.selected_glyph = glyph_id
                session.last_activity = datetime.utcnow()
                return True
        return False


# グローバルインスタンス
connection_manager = CollaborationConnectionManager()
