// webforge-ai-desktop/frontend/src/components/font/GlyphEditor.tsx

import React, { useCallback, useEffect, useRef, useState, useMemo } from 'react';
import { useGlyphTransform } from '../../hooks/useGlyphTransform';
import { MetricLines }       from './MetricLines';
import { SideBearingGuides } from './SideBearingGuides';
import { BezierLayer }       from './BezierLayer';
import { FloatingToolbar }   from './FloatingToolbar';
import './GlyphEditor.css';

import type { 
  GlyphData, 
  FontMetrics, 
  Vec2, 
  PointType, 
  EditorTool, 
  SelectionState 
} from './GlyphEditor.types';

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components — EditorTopBar
// ─────────────────────────────────────────────────────────────────────────────

interface EditorTopBarProps {
  tool:           EditorTool;
  onTool:         (t: EditorTool) => void;
  zoom:           number;
  onZoomIn:       () => void;
  onZoomOut:      () => void;
  onZoomFit:      () => void;
  showGrid:       boolean;
  onToggleGrid:   () => void;
  showGuides:     boolean;
  onToggleGuides: () => void;
  showFill:       boolean;
  onToggleFill:   () => void;
  snapToGrid:     boolean;
  onToggleSnap:   () => void;
  onUndo:         () => void;
  onRedo:         () => void;
}

const TOOLS: { key: EditorTool; icon: string; label: string }[] = [
  { key: 'select',  icon: 'ti-pointer',       label: 'Select (V)' },
  { key: 'pen',     icon: 'ti-pencil',        label: 'Pen (P)'    },
  { key: 'knife',   icon: 'ti-cut',           label: 'Knife (K)'  },
  { key: 'measure', icon: 'ti-ruler-measure', label: 'Measure (M)'},
];

const EditorTopBar: React.FC<EditorTopBarProps> = ({
  tool, onTool, zoom,
  onZoomIn, onZoomOut, onZoomFit,
  showGrid, onToggleGrid,
  showGuides, onToggleGuides,
  showFill, onToggleFill,
  snapToGrid, onToggleSnap,
  onUndo, onRedo,
}) => (
  <div className="wf-editor-topbar">
    {TOOLS.map(t => (
      <button
        key={t.key}
        className={`wf-editor-topbar__btn ${tool === t.key ? 'wf-editor-topbar__btn--active' : ''}`}
        onClick={() => onTool(t.key)}
        aria-pressed={tool === t.key}
        aria-label={t.label}
        title={t.label}
      >
        <i className={`ti ${t.icon}`} aria-hidden="true"/>
      </button>
    ))}

    <div className="wf-editor-topbar__sep" aria-hidden="true"/>

    <button className="wf-editor-topbar__btn" onClick={onUndo} aria-label="Undo (⌘Z)" title="Undo">
      <i className="ti ti-arrow-back-up" aria-hidden="true"/>
    </button>
    <button className="wf-editor-topbar__btn" onClick={onRedo} aria-label="Redo (⇧⌘Z)" title="Redo">
      <i className="ti ti-arrow-forward-up" aria-hidden="true"/>
    </button>

    <div className="wf-editor-topbar__sep" aria-hidden="true"/>

    <button
      className={`wf-editor-topbar__btn ${snapToGrid ? 'wf-editor-topbar__btn--active' : ''}`}
      onClick={onToggleSnap} aria-pressed={snapToGrid} aria-label="Snap to grid" title="Snap to grid">
      <i className="ti ti-grid-4x4" aria-hidden="true"/>
    </button>
    <button
      className={`wf-editor-topbar__btn ${showGuides ? 'wf-editor-topbar__btn--active' : ''}`}
      onClick={onToggleGuides} aria-pressed={showGuides} aria-label="Show guides" title="Show guides">
      <i className="ti ti-line-dashed" aria-hidden="true"/>
    </button>
    <button
      className={`wf-editor-topbar__btn ${showFill ? 'wf-editor-topbar__btn--active' : ''}`}
      onClick={onToggleFill} aria-pressed={showFill} aria-label="Show fill preview" title="Show fill">
      <i className="ti ti-circle-half-2" aria-hidden="true"/>
    </button>

    <div className="wf-editor-topbar__spacer"/>

    <span className="wf-editor-topbar__zoom">{Math.round(zoom * 100)}%</span>
    <button className="wf-editor-topbar__btn" onClick={onZoomIn}  aria-label="Zoom in"  title="Zoom in (+)"><i className="ti ti-zoom-in"  aria-hidden="true"/></button>
    <button className="wf-editor-topbar__btn" onClick={onZoomOut} aria-label="Zoom out" title="Zoom out (-)"><i className="ti ti-zoom-out" aria-hidden="true"/></button>
    <button className="wf-editor-topbar__btn" onClick={onZoomFit} aria-label="Zoom to fit" title="Zoom to fit (0)"><i className="ti ti-maximize" aria-hidden="true"/></button>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// GridLayer & クランプ関数
// ─────────────────────────────────────────────────────────────────────────────

const GridLayer: React.FC<{ w: number; h: number }> = ({ w, h }) => (
  <g aria-hidden="true">
    <defs>
      <pattern id="wf-smallgrid" width="20" height="20" patternUnits="userSpaceOnUse">
        <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,.026)" strokeWidth="0.5"/>
      </pattern>
      <pattern id="wf-grid" width="100" height="100" patternUnits="userSpaceOnUse">
        <rect width="100" height="100" fill="url(#wf-smallgrid)"/>
        <path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(255,255,255,.052)" strokeWidth="0.5"/>
      </pattern>
    </defs>
    <rect width={w} height={h} fill="url(#wf-grid)"/>
  </g>
);

const clamp = (val: number, min: number, max: number) => Math.max(min, Math.min(max, val));

// ─────────────────────────────────────────────────────────────────────────────
// GlyphEditor 本体
// ─────────────────────────────────────────────────────────────────────────────

export interface GlyphEditorProps {
  glyph:   GlyphData;
  metrics: FontMetrics;
  onPointMove?:      (cid: string, pid: string, pos: Vec2) => void;
  onHandleMove?:     (cid: string, pid: string, which: 'in' | 'out', pos: Vec2) => void;
  onPointTypeChange?:(cid: string, pid: string, type: PointType) => void;
  onAddPoint?:       (cid: string, pos: Vec2) => void;
  onDeletePoint?:    (cid: string, pid: string) => void;
  onUndo?:           () => void;
  onRedo?:           () => void;
}

export const GlyphEditor: React.FC<GlyphEditorProps> = ({
  glyph, metrics,
  onPointMove, onHandleMove, onPointTypeChange,
  onAddPoint, onDeletePoint,
  onUndo, onRedo,
}) => {
  const wrapRef  = useRef<HTMLDivElement>(null);
  const [canvasSize, setCanvasSize] = useState({ w: 680, h: 500 });

  useEffect(() => {
    const obs = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      const w = Math.floor(width);
      const h = Math.floor(height);
      
      // ✨ 魔法のストッパー：本当にサイズが変わった時（ピクセル単位）だけ更新する
      setCanvasSize(prev => {
        if (prev.w === w && prev.h === h) return prev; // 変化がなければ無限ループを遮断！
        return { w, h };
      });
    });
    if (wrapRef.current) obs.observe(wrapRef.current);
    return () => obs.disconnect();
  }, []);

  const [zoomFactor, setZoomFactor] = useState(1.0);
  const [pan, setPan] = useState<Vec2>({ x: 0, y: 0 });
  const [isSpaceDown, setIsSpaceDown] = useState(false);

  const zoomIn  = () => setZoomFactor(prev => Math.min(prev * 1.2, 8));
  const zoomOut = () => setZoomFactor(prev => Math.max(prev / 1.2, 0.1));
  const zoomFit = () => { setZoomFactor(1.0); setPan({ x: 0, y: 0 }); };

  const transform = useGlyphTransform({
    canvasW: canvasSize.w,
    canvasH: canvasSize.h,
    metrics,
    glyphWidth: glyph?.width || 1000,
    zoomFactor,
    pan,
  });

  const [tool,        setTool]        = useState<EditorTool>('select');
  const [showGrid,    setShowGrid]    = useState(true);
  const [showGuides,  setShowGuides]  = useState(true);
  const [showFill,    setShowFill]    = useState(false);
  const [snapToGrid,  setSnapToGrid]  = useState(false);

  const [selection, setSelection] = useState<SelectionState>({ contourId: null, pointIds: [] });
  const [cursor, setCursor] = useState<Vec2 | null>(null);

  type DragTarget =
    | { kind: 'anchor';  cid: string; pid: string; pointerId: number }
    | { kind: 'handle';  cid: string; pid: string; which: 'in' | 'out'; pointerId: number }
    | { kind: 'pan';     startX: number; startY: number; startPanX: number; startPanY: number; pointerId: number }
    | null;
  const dragRef = useRef<DragTarget>(null);

  const eventToFont = useCallback((e: React.PointerEvent | MouseEvent): Vec2 => {
    const rect = (e.target as Element).closest('svg')!.getBoundingClientRect();
    const svgX = e.clientX - rect.left;
    const svgY = e.clientY - rect.top;
    return transform.toFont({ x: svgX, y: svgY });
  }, [transform]);

  const handleAnchorPointerDown = useCallback((cid: string, pid: string, e: React.PointerEvent) => {
    e.stopPropagation();
    e.currentTarget.setPointerCapture(e.pointerId);
    dragRef.current = { kind: 'anchor', cid, pid, pointerId: e.pointerId };
    setSelection({ contourId: cid, pointIds: [pid] });
  }, []);

  const handleHandlePointerDown = useCallback((cid: string, pid: string, which: 'in' | 'out', e: React.PointerEvent) => {
    e.stopPropagation();
    e.currentTarget.setPointerCapture(e.pointerId);
    dragRef.current = { kind: 'handle', cid, pid, which, pointerId: e.pointerId };
  }, []);

  const handleSVGPointerDown = useCallback((e: React.PointerEvent<SVGSVGElement>) => {
    if (isSpaceDown || e.button === 1) {
      e.currentTarget.setPointerCapture(e.pointerId);
      dragRef.current = {
        kind: 'pan',
        startX: e.clientX,
        startY: e.clientY,
        startPanX: pan.x,
        startPanY: pan.y,
        pointerId: e.pointerId
      };
    }
  }, [isSpaceDown, pan]);

  const handleSVGPointerMove = useCallback((e: React.PointerEvent<SVGSVGElement>) => {
    setCursor(eventToFont(e));

    if (!dragRef.current) return;

    if (dragRef.current.kind === 'pan') {
      const dx = e.clientX - dragRef.current.startX;
      const dy = e.clientY - dragRef.current.startY;
      
      const nextX = clamp(dragRef.current.startPanX + dx, -2000, 2000);
      const nextY = clamp(dragRef.current.startPanY + dy, -2000, 2000);
      
      setPan({ x: nextX, y: nextY });
      return;
    }

    const fu = eventToFont(e);
    if (dragRef.current.kind === 'anchor') {
      onPointMove?.(dragRef.current.cid, dragRef.current.pid, fu);
    } else if (dragRef.current.kind === 'handle') {
      onHandleMove?.(dragRef.current.cid, dragRef.current.pid, dragRef.current.which, fu);
    }
  }, [eventToFont, onPointMove, onHandleMove]);

  const handleSVGPointerUp = useCallback((e: React.PointerEvent) => {
    if (dragRef.current) {
      try {
        (e.currentTarget as Element).releasePointerCapture(dragRef.current.pointerId);
      } catch (err) {
        // Ignored
      }
    }
    dragRef.current = null;
  }, []);

  const handleSVGClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (isSpaceDown) return;
    if ((e.target as Element).tagName === 'svg') {
      if (tool === 'pen' && selection.contourId) {
        onAddPoint?.(selection.contourId, eventToFont(e));
      } else {
        setSelection({ contourId: null, pointIds: [] });
      }
    }
  }, [tool, selection.contourId, eventToFont, isSpaceDown, onAddPoint]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.code === 'Space') { 
        e.preventDefault(); 
        setIsSpaceDown(true); 
        return; 
      }
      
      switch (e.key.toLowerCase()) {
        case 'v': setTool('select');  break;
        case 'p': setTool('pen');     break;
        case 'k': setTool('knife');   break;
        case 'm': setTool('measure'); break;
        case '+': case '=': zoomIn(); break;
        case '-': zoomOut(); break;
        case '0': zoomFit(); break;
        case 'delete':
        case 'backspace':
          if (selection.contourId && selection.pointIds[0]) {
            onDeletePoint?.(selection.contourId, selection.pointIds[0]);
          }
          break;
        case 'z':
          if (e.metaKey || e.ctrlKey) {
            e.shiftKey ? onRedo?.() : onUndo?.();
          }
          break;
      }
    };

    const onKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') setIsSpaceDown(false);
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selection]);

  const selectedPointType = useMemo(() => {
    if (!selection.contourId || selection.pointIds.length === 0) return undefined;
    const contour = glyph.contours.find(c => c.id === selection.contourId);
    return contour?.points.find(p => p.id === selection.pointIds[0])?.type;
  }, [glyph, selection]);

  const cursorStyle = isSpaceDown ? 'grab' : tool === 'pen' ? 'crosshair' : tool === 'knife' ? 'cell' : 'default';
  const anchorCount = glyph.contours.reduce((n, c) => n + c.points.length, 0);
  const pillText = `${glyph.char || '?'} — U+${glyph.unicode || '????'} · NouveauSans Regular · ${anchorCount} anchors`
    + (selection.pointIds.length > 0 ? ` · ${selection.pointIds.length} selected` : '');

  // ✨ 監視対象の ref を親の div ではなく、内側の canvas-wrap に移動しました！
  return (
    <div className="wf-glyph-editor" aria-label={`Glyph editor: ${glyph.char}`}>

      <EditorTopBar
        tool={tool}          onTool={setTool}
        zoom={zoomFactor}    onZoomIn={zoomIn} onZoomOut={zoomOut} onZoomFit={zoomFit}
        showGrid={showGrid}  onToggleGrid={() => setShowGrid(v => !v)}
        showGuides={showGuides} onToggleGuides={() => setShowGuides(v => !v)}
        showFill={showFill}  onToggleFill={() => setShowFill(v => !v)}
        snapToGrid={snapToGrid} onToggleSnap={() => setSnapToGrid(v => !v)}
        onUndo={onUndo ?? (() => {})}
        onRedo={onRedo ?? (() => {})}
      />

      <div className="wf-glyph-editor__canvas-wrap" ref={wrapRef}>
        <svg
          className="wf-glyph-editor__svg"
          width={canvasSize.w}
          height={canvasSize.h}
          style={{ cursor: cursorStyle }}
          onPointerDown={handleSVGPointerDown}
          onPointerMove={handleSVGPointerMove}
          onPointerUp={handleSVGPointerUp}
          onClick={handleSVGClick}
          role="img"
          aria-label={`Vector canvas for glyph ${glyph.char}`}
        >
          {showGrid && <GridLayer w={canvasSize.w} h={canvasSize.h}/>}

          {showGuides && (
            <>
              <MetricLines
                metrics={metrics}
                transform={transform}
                canvasW={canvasSize.w}
              />
              <SideBearingGuides
                metrics={metrics}
                glyphWidth={glyph.width}
                transform={transform}
                canvasH={canvasSize.h}
              />
            </>
          )}

          <BezierLayer
            glyph={glyph}
            transform={transform}
            selection={selection}
            tool={tool}
            showFill={showFill}
            onAnchorPointerDown={handleAnchorPointerDown}
            onHandlePointerDown={handleHandlePointerDown}
          />
        </svg>

        <FloatingToolbar
          selection={selection}
          currentPointType={selectedPointType}
          onSetPointType={type => {
            if (selection.contourId && selection.pointIds[0]) {
              onPointTypeChange?.(selection.contourId, selection.pointIds[0], type);
            }
          }}
          onAddPoint={() => {}}
          onDeletePoint={() => {
            if (selection.contourId && selection.pointIds[0]) {
              onDeletePoint?.(selection.contourId, selection.pointIds[0]);
            }
          }}
          onBreakPath={() => {}}
          onJoinPath={() => {}}
          onFlipH={() => {}}
          onFlipV={() => {}}
        />

        <div className="wf-glyph-editor__info-pill" aria-live="polite">
          {pillText}
        </div>

        {cursor && (
          <div className="wf-glyph-editor__coord-hud" aria-hidden="true">
            x: {Math.round(cursor.x)} &nbsp;|&nbsp; y: {Math.round(cursor.y)}
          </div>
        )}

      </div>
    </div>
  );
};