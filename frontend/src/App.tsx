// webforge-ai-desktop/frontend/src/App.tsx
import React, { useState } from 'react';
import { HashRouter, Routes, Route, Outlet } from 'react-router-dom';
import { CharacterGrid } from './components/font/CharacterGrid'; // パスは環境に合わせてください
import { useGlyphSelectionStore } from './store/glyphSelectionStore';
// 1. CSSのインポート
import './styles/global.css';
import './styles/tokens.css';

// 2. コンポーネントのインポート
import { AppShell } from './components/layout/AppShell';
import { FontStudio } from './pages/FontStudio';
import TopBar from './components/layout/TopBar';
import Sidebar from './components/layout/Sidebar';
import StatusBar from './components/layout/StatusBar';
import Dashboard from './pages/Dashboard';
import { AIPipelinePanel } from './components/font/AiPipelinepanel';
// ※ Claudeが生成したモックデータ（aiPipeline.mock.ts）から実体をインポートします
import { makeMockPayload } from './components/font/aiPipeline.mock';
// import { AiPipelinePayload } from './components/font/aiPipeline.types';
import ExportPanel from './pages/ExportPanel';
// 3. 型の仮定義（既存のまま）
// export type EditorMode = 'edit' | 'preview' | 'inspect';
export type EditorMode = 'edit' | 'preview' | 'metrics';
export type BackendStatus = 'connected' | 'disconnected' | 'syncing' | 'error';

export interface CollabUser {
  id: string;
  initials: string;
  color: string;
}

// ── 仮データ ──────────────
const DEMO_COLLAB_USERS: CollabUser[] = [
  { id: 'Yuki Kamura',  initials: 'YK', color: '#3a7ce8' },
  { id: 'Maria Ross',   initials: 'MR', color: '#e85d3a' },
  { id: 'Alex Sun',     initials: 'AS', color: '#3aaa6a' },
];

// ── Layout Component ─────────────────────────────────────────────────────────
// 全ページ共通の外枠（AppShell）を定義し、main部分に <Outlet /> を配置します。
// これにより、URLに応じて <Outlet /> の中身だけが切り替わります。
const MainLayout: React.FC<{
  editorMode: EditorMode;
  setEditorMode: (mode: EditorMode) => void;
  isSaving: boolean;
  handleSave: () => void;
  backendStatus: BackendStatus;
}> = ({ editorMode, setEditorMode, isSaving, handleSave, backendStatus }) => {
  
  // Zustandから選択状態を取得
  const { selectedUnicode, selectGlyph } = useGlyphSelectionStore();

  return (
    <AppShell
      topBar={
        <TopBar
          projectName="NouveauSans"
          variant="Regular"
          mode={editorMode}
          
          // onModeChange={setEditorMode}
          collabUsers={DEMO_COLLAB_USERS}
          isSaving={isSaving}
          onSave={handleSave}
        />
      }
      sidebar={
        // Sidebarは内部で <Link> を持つようになったため、propsは不要です
        <Sidebar />
      }
      main={
        // 🚨 ここがルーティングの穴になります 🚨
        <Outlet />
      }
      rightPanel={
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          height: '100%', 
          width: '380px', 
          backgroundColor: '#121212', 
          borderLeft: '1px solid rgba(255,255,255,0.05)' 
        }}>
          {/* 上半分：パイプラインパネル */}
          <div style={{ flexShrink: 0 }}>
            <AIPipelinePanel 
              payload={makeMockPayload()} 
              onToggle={(key, val) => console.log(`Toggle ${key}: ${val}`)}
            />
          </div>

          {/* 下半分：文字ピッカー（グリフパレット） */}
          {/* 保護色対策として、少しだけ背景色を浮かせ（#1a1a1a）、スクロール領域を確保します */}
          <div style={{ 
            flexGrow: 1, 
            overflowY: 'auto', 
            backgroundColor: '#1a1a1a', 
            borderTop: '2px solid #000' 
          }}>
            <div style={{ padding: '12px', fontSize: '0.85rem', color: '#888', letterSpacing: '1px' }}>
              GLYPH PALETTE
            </div>
            <CharacterGrid 
              compact={true}
              selectedUnicode={selectedUnicode}
              onSelect={selectGlyph} glyphMeta={undefined}            />
          </div>
        </div>
      }
      statusBar={
        <StatusBar
          backendStatus={backendStatus}
          gitBranch="main"
          engineStatus="kern engine ready"
          pointCount={12}
        />
      }
    />
  );
};

// ── App (Router Config) ───────────────────────────────────────────────────────

export default function App() {
  // 共通レイアウトで使うステート
  const [editorMode,    setEditorMode]    = useState<EditorMode>('edit');
  const [selectedGlyph, setSelectedGlyph] = useState<string | null>(null);
  const [isSaving,      setIsSaving]      = useState(false);

  const backendStatus: BackendStatus = 'connected';

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise(r => setTimeout(r, 1200));
    setIsSaving(false);
  };

  return (
    // Electron環境では HashRouter が必須です
    <HashRouter>
      <Routes>
        {/* 全てのルートの親として MainLayout を指定 */}
      <Route element={
          <MainLayout 
            editorMode={editorMode} 
            setEditorMode={setEditorMode}
            isSaving={isSaving}
            handleSave={handleSave}
            backendStatus={backendStatus}
          />
        }>
          
          {/* path="/" の時（ダッシュボード） */}
          <Route index element={<Dashboard />} />
          
          {/* 👇 新しく追加：プロジェクトを開いた時のルート */}
          <Route path="projects/:projectId" element={
              <FontStudio selectedGlyph={selectedGlyph ?? undefined} mode={editorMode} />
            } />

          {/* path="/builder" の時 */}
          <Route path="builder" element={<div style={{ color: 'white', padding: '40px' }}>🎨 サイトビルダー画面 (開発中)</div>} />
          
          {/* path="/font-studio" の時（FontStudio） */}
          <Route path="font-studio" element={
            // <FontStudio
            <FontStudio selectedGlyph={selectedGlyph ?? 'undefined'} mode={editorMode} />
             
           
            
          } />
          
          {/* その他のパス */}
          <Route path="chat-designer" element={<div style={{ color: 'white', padding: '40px' }}>💬 AIチャット画面 (開発中)</div>} />
          <Route path="export" element={<ExportPanel />} />

          {/* 👇 オマケ：今後真っ白にならないための「404 画面（迷子センター）」を追加 */}
          <Route path="*" element={
            <div style={{ color: 'white', padding: '40px' }}>
              <h2>🚧 404 Not Found</h2>
              <p>指定されたURLの画面が見つかりません。</p>
            </div>
          } />

        </Route>
      </Routes>
    </HashRouter>
  );
}