import React from 'react';
import './TopBar.css';

// 🔽 Claudeが探している型をここで export します
export type EditorMode = 'edit' | 'preview' | 'inspect' | 'metrics' | 'kern';

// App.tsx から渡される可能性のある Props を定義しておきます
interface TopBarProps {
  projectName?: string;
  variant?: string;
  mode?: EditorMode;
  onModeChange?: (mode: EditorMode) => void;
  collabUsers?: any[];
  isSaving?: boolean;
  onSave?: () => void;
}

const TopBar: React.FC<TopBarProps> = ({ 
  mode = 'edit', 
  onModeChange, 
  projectName = 'WebForge AI Desktop' 
}) => {
  const [isMaximized, setIsMaximized] = React.useState(false);

  const handleMinimize = () => {
    window.electronAPI?.window?.minimize?.();
  };

  const handleMaximize = () => {
    setIsMaximized(!isMaximized);
    window.electronAPI?.window?.maximize?.();
  };

  const handleClose = () => {
    window.electronAPI?.window?.close?.();
  };

  return (
    <header className="top-bar">
      <div className="top-bar-left">
        <h2 className="page-title">{projectName}</h2>
      </div>
      
      {/* 🔽 もしモード切替UIが必要ならここに追加できます */}
      {/* <div className="top-bar-center">
        {onModeChange && (
          <div className="mode-toggle">
            <button onClick={() => onModeChange('edit')} className={mode === 'edit' ? 'active' : ''}>Edit</button>
            <button onClick={() => onModeChange('preview')} className={mode === 'preview' ? 'active' : ''}>Preview</button>
          </div>
        )}
      </div> 
      */}

      <div className="top-bar-right">
        <div className="window-controls">
          <button 
            className="window-control-btn minimize"
            onClick={handleMinimize}
            title="最小化"
          >
            −
          </button>
          <button 
            className="window-control-btn maximize"
            onClick={handleMaximize}
            title="最大化"
          >
            □
          </button>
          <button 
            className="window-control-btn close"
            onClick={handleClose}
            title="閉じる"
          >
            ✕
          </button>
        </div>
      </div>
    </header>
  );
};

export default TopBar;