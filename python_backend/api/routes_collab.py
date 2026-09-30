from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
import json
import uuid
from datetime import datetime

from ..services.collab_engine.connection_manager import connection_manager, UserSession
from ..services.collab_engine.operation_transform import (
    Operation, OperationType, OperationContext, transform_engine
)

router = APIRouter(prefix="/collab", tags=["collaboration"])

# WebSocket コネクション管理（メモリ内）
# 本番環境では Redis を使用
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/{project_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str, user_id: str):
    """
    WebSocket エンドポイント
    接続: ws://localhost:8000/collab/ws/{project_id}/{user_id}
    """
    
    # セッション作成
    session = connection_manager.create_session(user_id, project_id)
    session_id = session.session_id
    
    try:
        await websocket.accept()
        active_connections[session_id] = websocket
        
        # ユーザーのコンテキスト初期化
        if project_id not in transform_engine.contexts:
            transform_engine.contexts[project_id] = {}
        
        context = OperationContext(
            user_id=user_id,
            session_id=session_id
        )
        transform_engine.contexts[project_id][session_id] = context
        
        # 接続時: アクティブユーザー一覧をブロードキャスト
        await broadcast_presence(project_id, {
            "type": "user_joined",
            "user_id": user_id,
            "session_id": session_id,
            "active_users": connection_manager.get_active_users(project_id)
        })
        
        # 接続中のメッセージ処理
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_message(message, session_id, project_id, user_id)
    
    except WebSocketDisconnect:
        # 切断時: セッション削除
        connection_manager.close_session(session_id)
        active_connections.pop(session_id, None)
        
        await broadcast_presence(project_id, {
            "type": "user_left",
            "user_id": user_id,
            "session_id": session_id,
            "active_users": connection_manager.get_active_users(project_id)
        })


async def handle_message(message: dict, session_id: str, project_id: str, user_id: str):
    """受信メッセージの処理"""
    msg_type = message.get("type")
    
    if msg_type == "operation":
        # ユーザーの編集操作
        await handle_operation(message, session_id, project_id, user_id)
    
    elif msg_type == "presence":
        # ユーザープレゼンス（カーソル位置など）更新
        cursor_x = message.get("cursor", {}).get("x", 0)
        cursor_y = message.get("cursor", {}).get("y", 0)
        glyph_id = message.get("selected_glyph")
        
        connection_manager.update_presence(session_id, cursor_x, cursor_y, glyph_id)
        
        # 他のユーザーにブロードキャスト
        await broadcast_presence(project_id, {
            "type": "cursor_moved",
            "user_id": user_id,
            "session_id": session_id,
            "cursor": {"x": cursor_x, "y": cursor_y},
            "selected_glyph": glyph_id
        })
    
    elif msg_type == "sync_request":
        # クライアントが最新状態をリクエスト
        await handle_sync_request(message, session_id, project_id)


async def handle_operation(message: dict, session_id: str, project_id: str, user_id: str):
    """編集操作を処理して他のユーザーに配信"""
    
    # 操作オブジェクトを構築
    op = Operation(
        id=str(uuid.uuid4()),
        type=OperationType(message.get("operation_type")),
        user_id=user_id,
        session_id=session_id,
        project_id=project_id,
        glyph_id=message.get("glyph_id"),
        timestamp=datetime.utcnow().timestamp(),
        content=message.get("content", {}),
        client_version=message.get("client_version", 0)
    )
    
    # 操作を履歴に追加
    success, msg = transform_engine.apply_operation(op)
    
    if not success:
        websocket = active_connections.get(session_id)
        if websocket:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": msg
            }))
        return
    
    # 他のユーザーにブロードキャスト
    await broadcast_operation(project_id, session_id, op.to_dict())


async def handle_sync_request(message: dict, session_id: str, project_id: str):
    """クライアントの同期リクエストに応答"""
    client_version = message.get("client_version", 0)
    
    # サーバー版以降の操作を取得
    operations = transform_engine.get_all_operations(project_id, client_version)
    
    websocket = active_connections.get(session_id)
    if websocket:
        await websocket.send_text(json.dumps({
            "type": "sync_response",
            "operations": [op.to_dict() for op in operations],
            "server_version": len(operations) + client_version
        }))


async def broadcast_operation(project_id: str, sender_session_id: str, operation: dict):
    """プロジェクト内の全ユーザーに操作をブロードキャスト（送信者除外）"""
    if project_id not in connection_manager.active_sessions:
        return
    
    for session_id, session in connection_manager.active_sessions[project_id].items():
        if session_id != sender_session_id:
            websocket = active_connections.get(session_id)
            if websocket:
                try:
                    await websocket.send_text(json.dumps({
                        "type": "remote_operation",
                        "operation": operation,
                        "sender_user_id": session.user_id
                    }))
                except:
                    pass  # 接続が失われている可能性


async def broadcast_presence(project_id: str, message: dict):
    """プロジェクト内の全ユーザーにプレゼンス情報をブロードキャスト"""
    if project_id not in connection_manager.active_sessions:
        return
    
    for session_id in connection_manager.active_sessions[project_id].keys():
        websocket = active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                pass
