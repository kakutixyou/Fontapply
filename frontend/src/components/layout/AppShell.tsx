/**
 * AppShell.tsx
 *
 * FigmaやVS Code風の「リサイザブル3ペインレイアウト」
 * サードパーティUIライブラリ不使用 — 純粋なReact + CSS
 *
 * レイアウト構造:
 *   TopBar (固定 44px)
 *   ├── Sidebar (リサイズ可 min:160 max:320)
 *   ├── [resize handle]
 *   ├── Main Canvas (flex:1)
 *   ├── [resize handle]
 *   └── Right Panel (リサイズ可 min:180 max:360)
 *   StatusBar (固定 24px)
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import './AppShell.css';

interface AppShellProps {
  topBar: React.ReactNode;
  sidebar: React.ReactNode;
  main: React.ReactNode;
  rightPanel: React.ReactNode;
  statusBar: React.ReactNode;
}

const SIDEBAR_MIN = 160;
const SIDEBAR_MAX = 320;
const SIDEBAR_DEFAULT = 200;

const RIGHTPANEL_MIN = 180;
const RIGHTPANEL_MAX = 360;
const RIGHTPANEL_DEFAULT = 220;

export const AppShell: React.FC<AppShellProps> = ({
  topBar, sidebar, main, rightPanel, statusBar,
}) => {
  const [sidebarW, setSidebarW] = useState(SIDEBAR_DEFAULT);
  const [rightPanelW, setRightPanelW] = useState(RIGHTPANEL_DEFAULT);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);

  const draggingLeft  = useRef<boolean>(false);
  const draggingRight = useRef<boolean>(false);
  const startX        = useRef<number>(0);
  const startW        = useRef<number>(0);

  /* ── Left resize handle ── */
  const onLeftMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    draggingLeft.current = true;
    startX.current = e.clientX;
    startW.current = sidebarW;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [sidebarW]);

  /* ── Right resize handle ── */
  const onRightMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    draggingRight.current = true;
    startX.current = e.clientX;
    startW.current = rightPanelW;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [rightPanelW]);

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (draggingLeft.current) {
        const delta = e.clientX - startX.current;
        setSidebarW(Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, startW.current + delta)));
      }
      if (draggingRight.current) {
        const delta = startX.current - e.clientX;
        setRightPanelW(Math.min(RIGHTPANEL_MAX, Math.max(RIGHTPANEL_MIN, startW.current + delta)));
      }
    };
    const onMouseUp = () => {
      draggingLeft.current = false;
      draggingRight.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, []);

  /* ── Keyboard shortcut: ⌘B sidebar, ⌘] right panel ── */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        setSidebarCollapsed(v => !v);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === ']') {
        e.preventDefault();
        setRightPanelCollapsed(v => !v);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const effectiveSidebarW    = sidebarCollapsed    ? 0 : sidebarW;
  const effectiveRightPanelW = rightPanelCollapsed ? 0 : rightPanelW;

  return (
    <div className="wf-shell">
      {/* TopBar */}
      <div className="wf-shell__topbar">{topBar}</div>

      {/* Body */}
      <div className="wf-shell__body">

        {/* Left Sidebar */}
        <aside
          className={`wf-shell__sidebar ${sidebarCollapsed ? 'wf-shell__sidebar--collapsed' : ''}`}
          style={{ width: effectiveSidebarW }}
          aria-label="Left sidebar"
        >
          <div className="wf-shell__sidebar-inner" style={{ width: sidebarW }}>
            {sidebar}
          </div>
        </aside>

        {/* Left resize handle */}
        {!sidebarCollapsed && (
          <div
            className="wf-shell__resize-handle wf-shell__resize-handle--left"
            onMouseDown={onLeftMouseDown}
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize sidebar"
            title="Drag to resize · ⌘B to toggle"
          />
        )}

        {/* Main area */}
        <main className="wf-shell__main" aria-label="Canvas editor">
          {main}
        </main>

        {/* Right resize handle */}
        {!rightPanelCollapsed && (
          <div
            className="wf-shell__resize-handle wf-shell__resize-handle--right"
            onMouseDown={onRightMouseDown}
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize properties panel"
            title="Drag to resize · ⌘] to toggle"
          />
        )}

        {/* Right Panel */}
        <aside
          className={`wf-shell__rightpanel ${rightPanelCollapsed ? 'wf-shell__rightpanel--collapsed' : ''}`}
          style={{ width: effectiveRightPanelW }}
          aria-label="Properties panel"
        >
          <div className="wf-shell__rightpanel-inner" style={{ width: rightPanelW }}>
            {rightPanel}
          </div>
        </aside>

      </div>

      {/* StatusBar */}
      <div className="wf-shell__statusbar">{statusBar}</div>
    </div>
  );
};