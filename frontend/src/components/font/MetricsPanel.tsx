import type { FontMetrics } from '../../../../shared/types/font';

export interface MetricsPanelProps {
  metrics: FontMetrics;
  onChange: (metrics: FontMetrics) => void;
}

const LATIN_PRESET: Required<FontMetrics> = {
  upm: 1000,
  ascender: 800,
  descender: -200,
  cap_height: 700,
  x_height: 520,
  line_gap: 0,
};

const CJK_PRESET: Required<FontMetrics> = {
  upm: 1000,
  ascender: 880,
  descender: -120,
  cap_height: 880,
  x_height: 760,
  line_gap: 0,
};

const SLIDER_FIELDS: Array<{ key: keyof FontMetrics; label: string; min: number; max: number }> = [
  { key: 'ascender', label: 'Ascender', min: 100, max: 1200 },
  { key: 'descender', label: 'Descender', min: -600, max: -10 },
  { key: 'cap_height', label: 'Cap Height', min: 100, max: 1200 },
  { key: 'x_height', label: 'X Height', min: 100, max: 1200 },
  { key: 'line_gap', label: 'Line Gap', min: 0, max: 600 },
];

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

/** Font metrics editor with presets and live metric preview. */
export function MetricsPanel({ metrics, onChange }: MetricsPanelProps) {
  const current: Required<FontMetrics> = {
    upm: metrics.upm ?? LATIN_PRESET.upm,
    ascender: metrics.ascender ?? LATIN_PRESET.ascender,
    descender: metrics.descender ?? LATIN_PRESET.descender,
    cap_height: metrics.cap_height ?? LATIN_PRESET.cap_height,
    x_height: metrics.x_height ?? LATIN_PRESET.x_height,
    line_gap: metrics.line_gap ?? LATIN_PRESET.line_gap,
  };
  const capHeightRatioPercent = Math.min(100, Math.max(0, (current.cap_height / current.upm) * 100));

  const update = (key: keyof FontMetrics, raw: string, min?: number, max?: number) => {
    const parsed = Number(raw);
    if (Number.isNaN(parsed)) {
      return;
    }

    onChange({
      ...current,
      [key]: min === undefined || max === undefined ? parsed : clamp(parsed, min, max),
    });
  };

  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">Metrics</h3>
        <div className="flex gap-2">
          <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => onChange(LATIN_PRESET)}>
            Latin
          </button>
          <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => onChange(CJK_PRESET)}>
            CJK
          </button>
        </div>
      </div>

      <label className="block text-sm text-slate-700">
        <span className="mb-1 block font-medium">UPM (units per em)</span>
        <input
          type="number"
          min={16}
          max={16384}
          value={current.upm}
          className="w-full rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) => update('upm', event.target.value, 16, 16384)}
        />
      </label>

      {SLIDER_FIELDS.map((field) => (
        <label key={field.key} className="block text-sm text-slate-700">
          <span className="mb-1 block font-medium">{field.label}: {current[field.key]}</span>
          <input
            type="range"
            min={field.min}
            max={field.max}
            value={current[field.key]}
            className="w-full"
            onChange={(event) => update(field.key, event.target.value, field.min, field.max)}
          />
        </label>
      ))}

      <div className="rounded border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
        <div>
          Metrics overview: ascender {current.ascender} / descender {Math.abs(current.descender)} / cap height{' '}
          {current.cap_height}
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded bg-slate-200">
          <div
            className="h-full bg-blue-500"
            style={{ width: `${capHeightRatioPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default MetricsPanel;
