/**
 * FloatingToolbar.tsx
 *
 * キャンバス右上に float するコンテキストツールバー。
 * 選択中のポイントに対してタイプ変換・追加/削除・パス操作・反転 を提供。
 *
 * position: absolute — 親 (<div class="wf-canvas-wrap">) が
 * position: relative である必要がある。
 */

import React from 'react';
import type { PointType, SelectionState } from './GlyphEditor.types';
import './FloatingToolbar.css';

interface FloatingToolbarProps {
  selection: SelectionState;
  /** 選択中ポイントのタイプ (複数選択時は最初のものを使用) */
  currentPointType: PointType | undefined;
  onSetPointType:     (type: PointType) => void;
  onAddPoint:         () => void;
  onDeletePoint:      () => void;
  onBreakPath:        () => void;
  onJoinPath:         () => void;
  onFlipH:            () => void;
  onFlipV:            () => void;
}

interface ToolBtn {
  icon:     string;
  label:    string;
  action:   () => void;
  active?:  boolean;
  disabled?: boolean;
}

export const FloatingToolbar: React.FC<FloatingToolbarProps> = ({
  selection, currentPointType,
  onSetPointType, onAddPoint, onDeletePoint,
  onBreakPath, onJoinPath, onFlipH, onFlipV,
}) => {
  const hasSelection = selection.pointIds.length > 0;

  const groups: ToolBtn[][] = [
    // ── ポイントタイプ変換 ──
    [
      {
        icon:   'ti-circle',
        label:  'Smooth point',
        action: () => onSetPointType('smooth'),
        active: currentPointType === 'smooth',
        disabled: !hasSelection,
      },
      {
        icon:   'ti-square',
        label:  'Corner point',
        action: () => onSetPointType('corner'),
        active: currentPointType === 'corner',
        disabled: !hasSelection,
      },
      
{
        icon:   'ti-triangle',
        label:  'Tangent point',
        action: () => onSetPointType('tangent'), // 🚨 'tangent' は新しい PointType に無いかも？
        active: currentPointType === 'tangent',
        disabled: !hasSelection,
      },
      
    ],
    // ── 追加 / 削除 ──
    [
      { icon: 'ti-plus',   label: 'Add anchor point',    action: onAddPoint    },
      { icon: 'ti-minus',  label: 'Delete anchor point', action: onDeletePoint, disabled: !hasSelection },
    ],
    // ── パス操作 ──
    [
      { icon: 'ti-scissors', label: 'Break path at point', action: onBreakPath, disabled: !hasSelection },
      { icon: 'ti-link',     label: 'Join paths',          action: onJoinPath  },
    ],
    // ── 変形 ──
    [
      { icon: 'ti-flip-horizontal', label: 'Flip horizontal', action: onFlipH },
      { icon: 'ti-flip-vertical',   label: 'Flip vertical',   action: onFlipV },
    ],
  ];

  return (
    <div className="wf-float-toolbar" role="toolbar" aria-label="Point tools">
      {groups.map((group, gi) => (
        <React.Fragment key={gi}>
          {gi > 0 && <div className="wf-float-toolbar__sep" aria-hidden="true"/>}
          {group.map(btn => (
            <button
              key={btn.label}
              className={`wf-float-toolbar__btn ${btn.active ? 'wf-float-toolbar__btn--active' : ''}`}
              onClick={btn.action}
              disabled={btn.disabled}
              aria-label={btn.label}
              title={btn.label}
            >
              <i className={`ti ${btn.icon}`} aria-hidden="true"/>
            </button>
          ))}
        </React.Fragment>
      ))}
    </div>
  );
};