import React from 'react';
import { UserCursor } from '../../hooks/usePresence';

interface UserPresenceIndicatorProps {
  cursor: UserCursor;
}

const UserPresenceIndicator: React.FC<UserPresenceIndicatorProps> = ({ cursor }) => {
  const { user_id, color, cursor_position, selected_glyph } = cursor;

  return (
    <div className="user-presence-indicator">
      <div
        className="user-avatar"
        style={{
          backgroundColor: color,
          borderColor: color
        }}
      >
        {user_id.charAt(0).toUpperCase()}
      </div>
      <div className="user-info">
        <div className="user-name">{user_id}</div>
        <div className="user-position">
          ({cursor_position.x}, {cursor_position.y})
        </div>
        {selected_glyph && (
          <div className="user-glyph">📝 {selected_glyph}</div>
        )}
      </div>

      <style>{`
        .user-presence-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px;
          border-bottom: 1px solid #eee;
          font-size: 12px;
        }

        .user-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          border: 2px solid;
          flex-shrink: 0;
        }

        .user-info {
          flex: 1;
        }

        .user-name {
          font-weight: bold;
          color: #333;
        }

        .user-position {
          color: #999;
          font-size: 11px;
        }

        .user-glyph {
          color: #666;
          margin-top: 4px;
        }
      `}</style>
    </div>
  );
};

export default UserPresenceIndicator;
