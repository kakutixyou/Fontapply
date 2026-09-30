import type { CapStyle, JoinStyle, StrokeParams } from '../../../../shared/types/font';

export interface StrokeEditorProps {
  stroke: StrokeParams;
  onChange: (stroke: StrokeParams) => void;
}

const CAP_STYLES: Array<{ value: CapStyle; label: string }> = [
  { value: 'butt', label: 'Butt' },
  { value: 'round', label: 'Round' },
  { value: 'square', label: 'Square' },
];

const JOIN_STYLES: Array<{ value: JoinStyle; label: string }> = [
  { value: 'bevel', label: 'Bevel' },
  { value: 'round', label: 'Round' },
  { value: 'miter', label: 'Miter' },
];
const PREVIEW_STROKE_DIVISOR = 14;
const MIN_PREVIEW_STROKE_WIDTH = 2;

/** Stroke editor for weight/cap/join with inline SVG feedback. */
export function StrokeEditor({ stroke, onChange }: StrokeEditorProps) {
  const current: Required<StrokeParams> = {
    weight: stroke.weight ?? 80,
    cap_style: stroke.cap_style ?? 'round',
    join_style: stroke.join_style ?? 'round',
  };

  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-800">Stroke</h3>

      <label className="block text-sm text-slate-700">
        <span className="mb-1 block font-medium">Weight: {current.weight}</span>
        <input
          type="range"
          min={10}
          max={200}
          value={current.weight}
          className="w-full"
          onChange={(event) => onChange({ ...current, weight: Number(event.target.value) })}
        />
      </label>

      <label className="block text-sm text-slate-700">
        <span className="mb-1 block font-medium">Cap Style</span>
        <select
          value={current.cap_style}
          className="w-full rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) => onChange({ ...current, cap_style: event.target.value as CapStyle })}
        >
          {CAP_STYLES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="block text-sm text-slate-700">
        <span className="mb-1 block font-medium">Join Style</span>
        <select
          value={current.join_style}
          className="w-full rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) => onChange({ ...current, join_style: event.target.value as JoinStyle })}
        >
          {JOIN_STYLES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <div className="rounded border border-slate-200 bg-slate-50 p-3">
        <svg viewBox="0 0 220 90" className="h-24 w-full">
          <line
            x1={25}
            y1={30}
            x2={195}
            y2={30}
            stroke="#1d4ed8"
            strokeWidth={Math.max(MIN_PREVIEW_STROKE_WIDTH, current.weight / PREVIEW_STROKE_DIVISOR)}
            strokeLinecap={current.cap_style}
          />
          <polyline
            points="30,75 110,45 190,75"
            fill="none"
            stroke="#0f766e"
            strokeWidth={Math.max(MIN_PREVIEW_STROKE_WIDTH, current.weight / PREVIEW_STROKE_DIVISOR)}
            strokeLinejoin={current.join_style}
            strokeLinecap="round"
          />
        </svg>
      </div>
    </div>
  );
}

export default StrokeEditor;
