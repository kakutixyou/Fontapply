// src/pages/ExportPanel.tsx
import React from 'react';
import { useFontStore } from '../store/fontStore';

export default function ExportPanel() {
  const currentGlyph = useFontStore((state: any) => state.currentGlyph);
  
  const metrics = useFontStore((state: any) => state.metrics) || {
    capHeight: 680,
    descender: -200,
  };

  const downloadFile = (filename: string, content: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    if (!currentGlyph) return;
    const jsonString = JSON.stringify(currentGlyph, null, 2);
    downloadFile(`glyph_${currentGlyph.unicode || 'export'}.json`, jsonString, 'application/json');
  };

  // ── 修正：データの x, y に安全にアクセスする ──
  const getX = (pt: any) => pt.pos?.x ?? pt.x ?? 0;
  const getY = (pt: any) => pt.pos?.y ?? pt.y ?? 0;

  const handleExportSVG = () => {
    if (!currentGlyph) return;
    let pathData = '';
    const capH = metrics.capHeight || 680;

    currentGlyph.contours?.forEach((contour: any) => {
      if (!contour.points || contour.points.length === 0) return;

      const start = contour.points[0];
      pathData += `M ${getX(start)} ${capH - getY(start)} `;

      for (let i = 1; i < contour.points.length; i++) {
        const prev = contour.points[i - 1];
        const curr = contour.points[i];

        if (prev.type === 'smooth' || curr.type === 'smooth') {
          // ハンドルの座標も pos と同様にフォールバック処理を入れる
          const cp1x = prev.handle_out?.x ?? prev.handleOut?.x ?? getX(prev);
          const cp1y = prev.handle_out?.y ?? prev.handleOut?.y ?? getY(prev);
          const cp2x = curr.handle_in?.x ?? curr.handleIn?.x ?? getX(curr);
          const cp2y = curr.handle_in?.y ?? curr.handleIn?.y ?? getY(curr);

          pathData += `C ${cp1x} ${capH - cp1y}, ${cp2x} ${capH - cp2y}, ${getX(curr)} ${capH - getY(curr)} `;
        } else {
          pathData += `L ${getX(curr)} ${capH - getY(curr)} `;
        }
      }

      if (contour.closed) {
        const last = contour.points[contour.points.length - 1];
        const first = contour.points[0];
        if (last.type === 'smooth' || first.type === 'smooth') {
          const cp1x = last.handle_out?.x ?? last.handleOut?.x ?? getX(last);
          const cp1y = last.handle_out?.y ?? last.handleOut?.y ?? getY(last);
          const cp2x = first.handle_in?.x ?? first.handleIn?.x ?? getX(first);
          const cp2y = first.handle_in?.y ?? first.handleIn?.y ?? getY(first);
          pathData += `C ${cp1x} ${capH - cp1y}, ${cp2x} ${capH - cp2y}, ${getX(first)} ${capH - getY(first)} `;
        }
        pathData += 'Z ';
      }
    });

    const viewBoxHeight = capH - (metrics.descender || -200);
    const svgString = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 ${metrics.descender || -200} ${currentGlyph.width} ${viewBoxHeight}">
  <path d="${pathData.trim()}" fill="#ffffff" />
</svg>`;

    downloadFile(`glyph_${currentGlyph.unicode || 'export'}.svg`, svgString, 'image/svg+xml');
  };

  const handleExportPy = () => {
    if (!currentGlyph) return;
    
    let pyCode = `# 手動編集されたカスタムグリフデータ\n`;
    pyCode += `CUSTOM_GLYPH_${currentGlyph.unicode} = {\n`;
    pyCode += `    "char": "${currentGlyph.char}",\n`;
    pyCode += `    "unicode": "${currentGlyph.unicode}",\n`;
    pyCode += `    "width": ${currentGlyph.width},\n`;
    pyCode += `    "contours": [\n`;

    currentGlyph.contours?.forEach((contour: any, idx: number) => {
      pyCode += `        {\n`;
      pyCode += `            "id": "c${idx}",\n`;
      pyCode += `            "closed": ${contour.closed ? 'True' : 'False'},\n`;
      pyCode += `            "points": [\n`;
      
      contour.points?.forEach((pt: any) => {
        if (pt.type === 'corner') {
          pyCode += `                corner("${pt.id}", ${getX(pt)}, ${getY(pt)}),\n`;
        } else {
          const hInX = pt.handle_in?.x ?? pt.handleIn?.x;
          const hInY = pt.handle_in?.y ?? pt.handleIn?.y;
          const hOutX = pt.handle_out?.x ?? pt.handleOut?.x;
          const hOutY = pt.handle_out?.y ?? pt.handleOut?.y;

          const hiStr = (hInX !== undefined && hInY !== undefined) ? `(${hInX}, ${hInY})` : 'None';
          const hoStr = (hOutX !== undefined && hOutY !== undefined) ? `(${hOutX}, ${hOutY})` : 'None';
          pyCode += `                smooth("${pt.id}", ${getX(pt)}, ${getY(pt)}, hi=${hiStr}, ho=${hoStr}),\n`;
        }
      });

      pyCode += `            ]\n`;
      pyCode += `        },\n`;
    });

    pyCode += `    ]\n}\n`;

    downloadFile(`custom_U${currentGlyph.unicode}.py`, pyCode, 'text/x-python');
  };

  const buttonStyle = {
    padding: '10px 20px',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: currentGlyph ? 'pointer' : 'not-allowed',
    fontWeight: 'bold' as const,
    opacity: currentGlyph ? 1 : 0.5,
    transition: 'background-color 0.2s',
  };

  return (
    <div style={{ color: 'white', padding: '40px', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ borderBottom: '1px solid #333', paddingBottom: '10px' }}>
        📤 マルチフォーマット・エクスポート
      </h2>
      <p style={{ color: '#aaa', marginBottom: '25px' }}>
        現在選択されているグリフデータを各種フォーマットでブラウザに直接ダウンロードします。
      </p>

      <div style={{ display: 'flex', gap: '15px', marginBottom: '30px' }}>
        <button onClick={handleExportJSON} disabled={!currentGlyph} style={{ ...buttonStyle, backgroundColor: '#4a5568' }}>
          ⚙️ JSON を保存
        </button>
        <button onClick={handleExportSVG} disabled={!currentGlyph} style={{ ...buttonStyle, backgroundColor: '#38a169' }}>
          🎨 SVG を保存
        </button>
        <button onClick={handleExportPy} disabled={!currentGlyph} style={{ ...buttonStyle, backgroundColor: '#3182ce' }}>
          🐍 Pythonコード を保存
        </button>
      </div>

      <h3 style={{ fontSize: '14px', color: '#888', marginBottom: '10px' }}>現在のデータプレビュー</h3>
      <div style={{ backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '8px', border: '1px solid #333' }}>
        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word', color: '#a6e22e', fontFamily: 'monospace' }}>
          {currentGlyph 
            ? JSON.stringify(currentGlyph, null, 2) 
            : '※ グリフデータが選択されていません。フォント作成タブで文字を選択してください。'}
        </pre>
      </div>
    </div>
  );
}