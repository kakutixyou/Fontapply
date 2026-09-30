# python_backend/api/routes_pipeline.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.font_engine.analytics_engine import analytics_engine
import json

router = APIRouter()

@router.websocket("/ws/pipeline")
async def pipeline_websocket(websocket: WebSocket):
    await websocket.accept()
    
    # 現在のトグル状態を保持
    active_toggles = {
        "vectorExtract": True,
        "skeletonAnalysis": True,
        "velocityTrack": False
    }

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")

            if action == "SET_TOGGLE":
                active_toggles[payload["key"]] = payload["enabled"]
                await websocket.send_json({"log": f"[CONFIG]: {payload['key']} set to {payload['enabled']}"})

            elif action == "REQUEST_EXTRACT":
                unicode_char = payload.get("unicode", "U+0000")
                # 解析エンジンを回し、結果を逐次送信
                async for update in analytics_engine.extract_glyph_features(unicode_char, active_toggles):
                    await websocket.send_json(update)

    except WebSocketDisconnect:
        print("Pipeline WebSocket disconnected")