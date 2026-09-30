// webforge-ai-desktop/frontend/src/components/layout/StatusBar.tsx
import React from 'react';
import './StatusBar.css';
type BackendStatus = 'connected' | 'disconnected' | 'syncing' | 'error';

export interface StatusBarProps {
  backendStatus: BackendStatus;
  gitBranch: string;
  engineStatus: string;
  pointCount: number;
}

// コンポーネントにPropsの型を適用する
export const StatusBar: React.FC<StatusBarProps> = ({ backendStatus }) => {
    const connectionStatusText = {
      connected: 'Python 接続済み',
      disconnected: 'Python 未接続',
      syncing: 'Python 接続確認中',
      error: 'Python 接続エラー',
    }[backendStatus];

  return (
 
    <footer className="status-bar">
      <div className="status-left">
        <span className={`status-indicator ${backendStatus}`}>
          ● {connectionStatusText}
        </span>
      </div>
      
      <div className="status-center">
        <span className="processing-status">待機中</span>
      </div>
      
      <div className="status-right">
        <span className="app-version">v0.1.0-alpha</span>
      </div>
    </footer>
  
  );
};
// const StatusBar: React.FC = () => {
//   const [pythonConnected, setPythonConnected] = useState(false);
//   const [processingStatus, setProcessingStatus] = useState('待機中');

//   useEffect(() => {
//     // TODO: Python バックエンド接続状態を監視するロジック
//     // 初期状態は 'false' に設定
//   }, []);

//   const connectionStatusClass = pythonConnected ? 'connected' : 'disconnected';
//   const connectionStatusText = pythonConnected ? 'Python 接続済み' : 'Python 未接続';

//   return (
//     <footer className="status-bar">
//       <div className="status-left">
//         <span className={`status-indicator ${connectionStatusClass}`}>
//           ● {connectionStatusText}
//         </span>
//       </div>
      
//       <div className="status-center">
//         <span className="processing-status">{processingStatus}</span>
//       </div>
      
//       <div className="status-right">
//         <span className="app-version">v0.1.0-alpha</span>
//       </div>
//     </footer>
//   );
// };

export default StatusBar;
