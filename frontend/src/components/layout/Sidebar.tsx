// webforge-ai-desktop/frontend/src/components/layout/Sidebar.tsx
import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { CharacterGrid } from '../font/CharacterGrid'; 
import { useGlyphSelectionStore } from '../../store/glyphSelectionStore'; // パスは実際の構成に合わせてください
import './Sidebar.css';
import './Sidebar.css';

// electronAPIの型定義（必要に応じて types.d.ts に移動してください）
declare global {
  interface Window {
    electronAPI: any;
  }
}

const Sidebar: React.FC = () => {
  const location = useLocation();
  const isFontStudio = location.pathname.includes('font-studio');
  
  // これを追加：Zustandから選択状態と更新関数を取得
  const { selectedUnicode, selectGlyph } = useGlyphSelectionStore();

  // AI Pipeline の状態管理
  const [pipelineData, setPipelineData] = useState({
    pointsCollected: 12480,
    structuralFidelity: 94.2,
    status: 'AWAITING_STROKE', // IDLE, EXTRACTING, OPTIMIZED
    log: '[SYSTEM_LOG]: Ready for extraction.'
  });

  const [toggles, setToggles] = useState({
    vectorExtract: true,
    skeletonAnalysis: true,
    velocityTrack: false,
  });

  // バックエンドからのリアルタイムデータを受信
  useEffect(() => {
    if (window.electronAPI?.onPipelineUpdate) {
      const cleanup = window.electronAPI.onPipelineUpdate((payload: any) => {
        setPipelineData((prev) => ({ ...prev, ...payload }));
      });
      return cleanup; // アンマウント時にクリーンアップ
    }
  }, []);

  // トグルの切り替えとバックエンドへの通知
  const handleToggle = (key: keyof typeof toggles) => {
    const newVal = !toggles[key];
    setToggles((prev) => ({ ...prev, [key]: newVal }));
    if (window.electronAPI?.setPipelineToggle) {
      window.electronAPI.setPipelineToggle(key, newVal);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-header">
          <h1 className="app-title">WebForge AI</h1>
        </div>
        
        <nav className="sidebar-nav">
          <ul className="nav-list">
            <li className="nav-item">
              <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>📊 ダッシュボード</Link>
            </li>
            <li className="nav-item">
              <Link to="/builder" className={`nav-link ${location.pathname.includes('/builder') ? 'active' : ''}`}>🎨 サイトビルダー</Link>
            </li>
            <li className="nav-item">
              <Link to="/font-studio" className={`nav-link ${isFontStudio ? 'active' : ''}`}>🔤 フォント作成</Link>
            </li>
            <li className="nav-item">
              <Link to="/chat-designer" className={`nav-link ${location.pathname.includes('/chat-designer') ? 'active' : ''}`}>💬 AIチャット</Link>
            </li>
            <li className="nav-item">
              <Link to="/export" className={`nav-link ${location.pathname.includes('/export') ? 'active' : ''}`}>📤 エクスポート</Link>
            </li>
          </ul>
        </nav>
      </div>

      {/* フォントスタジオ起動時のみ表示されるプロ仕様のデータパイプラインUI */}
      {isFontStudio && (
        <div className="ai-pipeline-panel">
          <div className="panel-header">
            <span className="panel-title">NEURAL PIPELINE</span>
            <span className={`status-indicator ${pipelineData.status === 'EXTRACTING' ? 'pulse' : ''}`}></span>
          </div>
          <div className="sidebar-glyph-pane" style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', flex: 1, minHeight: '300px' }}>
            <div className="panel-header">
              <span className="panel-title">GLYPH PALETTE</span>
            </div>
            {/* compact=true を渡すことでサイドバー用のミニマル表示になります */}
            <CharacterGrid 
              compact={true} 
              selectedUnicode={selectedUnicode}
              onSelect={selectGlyph}
            />
          </div>
          <div className="metrics-container">
            <div className="metric-box">
              <span className="metric-label">DATA POINTS</span>
              <span className="metric-value font-mono">{pipelineData.pointsCollected.toLocaleString()}</span>
            </div>
            <div className="metric-box">
              <span className="metric-label">FIDELITY</span>
              <span className="metric-value font-mono accent-green">{pipelineData.structuralFidelity.toFixed(1)}%</span>
            </div>
          </div>

          <div className="toggles-container">
            <div className="toggle-row">
              <span className="toggle-label">Vector Extraction</span>
              <button 
                className={`toggle-btn ${toggles.vectorExtract ? 'on' : 'off'}`}
                onClick={() => handleToggle('vectorExtract')}
              />
            </div>
            <div className="toggle-row">
              <span className="toggle-label">Skeleton Analysis</span>
              <button 
                className={`toggle-btn ${toggles.skeletonAnalysis ? 'on' : 'off'}`}
                onClick={() => handleToggle('skeletonAnalysis')}
              />
            </div>
            <div className="toggle-row">
              <span className="toggle-label">Stroke Velocity</span>
              <button 
                className={`toggle-btn ${toggles.velocityTrack ? 'on' : 'off'}`}
                onClick={() => handleToggle('velocityTrack')}
              />
            </div>
          </div>

          <div className="terminal-log">
            <p>{pipelineData.log}</p>
          </div>
        </div>
      )}

      <div className="sidebar-footer">
        <p className="version">v0.1.0-alpha</p>
      </div>
    </aside>
  );
};

export default Sidebar;