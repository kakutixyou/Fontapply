import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useCollaboration } from '../../hooks/useCollaboration';
import { usePresence, UserCursor } from '../../hooks/usePresence';
import UserPresenceIndicator from './UserPresenceIndicator';

interface CollaborativeCanvasProps {
  projectId: string;
  onGlyphModified?: (glyphId: string, changes: any) => void;
}

const CollaborativeCanvas: React.FC<CollaborativeCanvasProps> = ({
  projectId,
  onGlyphModified
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedGlyph, setSelectedGlyph] = useState<string | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [glyphs, setGlyphs] = useState<any[]>([]);
  
  const { userCursors, updateUserCursor, removeUserCursor } = usePresence();

  // リモート操作を処理
  const handleRemoteOperation = useCallback((operation: any) => {
    if (operation.type === 'cursor_moved') {
      updateUserCursor(
        operation.user_id,
        operation.session_id,
        operation.cursor.x,
        operation.cursor.y,
        operation.selected_glyph
      );
    } else if (operation.type === 'user_left') {
      removeUserCursor(operation.session_id);
    }
  }, [updateUserCursor, removeUserCursor]);

  const { isConnected, sendOperation, updatePresence } = useCollaboration(
    handleRemoteOperation
  );

  // マウス移動時にプレゼンス更新
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (canvasRef.current) {
        const rect = canvasRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        setMousePos({ x, y });
        
        // 100ms ごとにプレゼンス更新（スロットリング）
        updatePresence(x, y, selectedGlyph || undefined);
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [selectedGlyph, updatePresence]);

  // キャンバス描画
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 背景クリア
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // グリッド描画
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    for (let i = 0; i < canvas.width; i += 50) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, canvas.height);
      ctx.stroke();
    }
    for (let i = 0; i < canvas.height; i += 50) {
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(canvas.width, i);
      ctx.stroke();
    }

    // グリフを描画
    glyphs.forEach(glyph => {
      drawGlyph(ctx, glyph, glyph.id === selectedGlyph);
    });

    // リモートユーザーのカーソルを描画
    userCursors.forEach(cursor => {
      drawUserCursor(ctx, cursor);
    });
  }, [glyphs, selectedGlyph, userCursors]);

  const drawGlyph = (
    ctx: CanvasRenderingContext2D,
    glyph: any,
    isSelected: boolean
  ) => {
    ctx.fillStyle = isSelected ? '#ff6b6b' : '#333333';
    ctx.font = `${glyph.size || 40}px sans-serif`;
    ctx.fillText(glyph.name || '?', 100, 100);

    if (isSelected) {
      ctx.strokeStyle = '#ff6b6b';
      ctx.lineWidth = 2;
      ctx.strokeRect(90, 80, 200, 100);
    }
  };

  const drawUserCursor = (ctx: CanvasRenderingContext2D, cursor: UserCursor) => {
    const { cursor_position, user_id, color } = cursor;
    const { x, y } = cursor_position;

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = color;
    ctx.font = '12px sans-serif';
    ctx.fillText(user_id, x + 10, y - 10);
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const clicked = glyphs.find(g => {
      return Math.abs(x - 100) < 100 && Math.abs(y - 100) < 50;
    });

    if (clicked) {
      setSelectedGlyph(clicked.id);
      updatePresence(x, y, clicked.id);
    }
  };

  return (
    <div className="collaborative-canvas-container">
      <div className="canvas-toolbar">
        <span>接続状態: {isConnected ? '✅ 接続中' : '❌ 接続中...'}</span>
      </div>

      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        onClick={handleCanvasClick}
        style={{
          border: '1px solid #ccc',
          cursor: 'crosshair',
          display: 'block',
          background: '#fafafa'
        }}
      />

      <div className="active-users-panel">
        <h3>参加ユーザー</h3>
        {userCursors.map(cursor => (
          <UserPresenceIndicator
            key={cursor.session_id}
            cursor={cursor}
          />
        ))}
      </div>

      <style>{`
        .collaborative-canvas-container {
          display: flex;
          gap: 20px;
          padding: 20px;
        }

        .canvas-toolbar {
          padding: 10px;
          background: #f0f0f0;
          border-radius: 4px;
          margin-bottom: 10px;
        }

        .active-users-panel {
          width: 200px;
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 10px;
          background: #f9f9f9;
        }

        .active-users-panel h3 {
          margin: 0 0 10px 0;
          font-size: 14px;
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default CollaborativeCanvas;
