import React, { useEffect, useState } from 'react';

interface ConflictNotificationProps {
  conflict: {
    type: string;
    field: string;
    yourValue: any;
    theirValue: any;
    theirUser: string;
  } | null;
  onResolved?: (choice: 'yours' | 'theirs') => void;
}

const ConflictNotification: React.FC<ConflictNotificationProps> = ({
  conflict,
  onResolved
}) => {
  const [visible, setVisible] = useState(!!conflict);

  useEffect(() => {
    setVisible(!!conflict);
    if (conflict) {
      const timeout = setTimeout(() => setVisible(false), 5000);
      return () => clearTimeout(timeout);
    }
  }, [conflict]);

  if (!visible || !conflict) return null;

  return (
    <div className="conflict-notification">
      <div className="conflict-header">
        ⚠️ 競合検出
      </div>
      <div className="conflict-content">
        <p>
          <strong>{conflict.theirUser}</strong> が
          <strong>{conflict.field}</strong> を変更しました。
        </p>
        <div className="conflict-values">
          <div className="your-value">
            あなた: <code>{JSON.stringify(conflict.yourValue)}</code>
          </div>
          <div className="their-value">
            相手: <code>{JSON.stringify(conflict.theirValue)}</code>
          </div>
        </div>
      </div>
      <div className="conflict-actions">
        <button onClick={() => {
          onResolved?.('yours');
          setVisible(false);
        }}>
          自分の変更を保持
        </button>
        <button onClick={() => {
          onResolved?.('theirs');
          setVisible(false);
        }}>
          相手の変更を採用
        </button>
      </div>

      <style>{`
        .conflict-notification {
          position: fixed;
          bottom: 20px;
          right: 20px;
          background: white;
          border: 2px solid #ff6b6b;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(255, 107, 107, 0.2);
          padding: 16px;
          max-width: 400px;
          z-index: 1000;
          animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        .conflict-header {
          font-weight: bold;
          color: #ff6b6b;
          margin-bottom: 8px;
        }

        .conflict-content {
          margin-bottom: 12px;
          color: #333;
          font-size: 14px;
        }

        .conflict-values {
          margin: 8px 0;
          background: #f5f5f5;
          padding: 8px;
          border-radius: 4px;
          font-size: 12px;
        }

        .your-value, .their-value {
          margin: 4px 0;
        }

        .conflict-actions {
          display: flex;
          gap: 8px;
        }

        .conflict-actions button {
          flex: 1;
          padding: 8px 12px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          font-weight: bold;
        }

        .conflict-actions button:first-child {
          background: #4ecdc4;
          color: white;
        }

        .conflict-actions button:last-child {
          background: #ff6b6b;
          color: white;
        }
      `}</style>
    </div>
  );
};

export default ConflictNotification;
