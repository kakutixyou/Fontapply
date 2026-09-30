import { useEffect, useRef, useCallback, useState } from 'react';
import { useParams } from 'react-router-dom';

interface Operation {
  id: string;
  type: string;
  glyph_id: string;
  user_id: string;
  content: Record<string, any>;
  timestamp: number;
}

interface RemoteOperation extends Operation {
  sender_user_id: string;
}

export const useCollaboration = (onRemoteOperation?: (op: RemoteOperation) => void) => {
  const { projectId } = useParams<{ projectId: string }>();
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [activeUsers, setActiveUsers] = useState<any[]>([]);
  const clientVersionRef = useRef(0);

  // WebSocket 接続
  useEffect(() => {
    if (!projectId) return;

    const userId = localStorage.getItem('userId') || 'anonymous';
    const apiBaseUrl =
      import.meta.env.VITE_DESIGN_API_BASE_URL ||
      import.meta.env.VITE_FONT_API_BASE_URL ||
      'http://127.0.0.1:8000';
    const wsBaseUrl = apiBaseUrl.replace(/^http/, 'ws').replace(/\/+$/, '');
    const wsUrl = `${wsBaseUrl}/collab/ws/${projectId}/${userId}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('✅ Collaboration WebSocket connected');
      setIsConnected(true);
      
      // サーバーに現在のバージョンを送信して同期
      ws.send(JSON.stringify({
        type: 'sync_request',
        client_version: clientVersionRef.current
      }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'remote_operation') {
        // リモートユーザーの操作を受信
        clientVersionRef.current++;
        onRemoteOperation?.(message.operation);

      } else if (message.type === 'user_joined' || message.type === 'user_left') {
        // ユーザープレゼンス更新
        setActiveUsers(message.active_users);

      } else if (message.type === 'cursor_moved') {
        // カーソル位置更新
        onRemoteOperation?.(message);

      } else if (message.type === 'sync_response') {
        // 同期レスポンス: 欠落していた操作を取得
        message.operations.forEach((op: Operation) => {
          // message.operations may lack sender_user_id required by RemoteOperation
          const remoteOp: RemoteOperation = {
            ...op,
            sender_user_id: (op as any).sender_user_id || op.user_id || 'system'
          };

          onRemoteOperation?.(remoteOp);
        });
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('❌ WebSocket closed');
      setIsConnected(false);
    };

    wsRef.current = ws;

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [projectId, onRemoteOperation]);

  // 操作を送信
  const sendOperation = useCallback((
    operationType: string,
    glyphId: string,
    content: Record<string, any>
  ) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    clientVersionRef.current++;

    wsRef.current.send(JSON.stringify({
      type: 'operation',
      operation_type: operationType,
      glyph_id: glyphId,
      content,
      client_version: clientVersionRef.current
    }));
  }, []);

  // プレゼンス更新（カーソル位置など）
  const updatePresence = useCallback((
    cursorX: number,
    cursorY: number,
    selectedGlyph?: string
  ) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    wsRef.current.send(JSON.stringify({
      type: 'presence',
      cursor: { x: cursorX, y: cursorY },
      selected_glyph: selectedGlyph
    }));
  }, []);

  return {
    isConnected,
    activeUsers,
    sendOperation,
    updatePresence
  };
};
