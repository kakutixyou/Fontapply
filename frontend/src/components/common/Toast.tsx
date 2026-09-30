export interface ToastProps {
  message: string;
  variant?: 'success' | 'error';
  onClose: () => void;
}

/** Dismissible toast message for success/error feedback. */
export function Toast({ message, variant = 'success', onClose }: ToastProps) {
  return (
    <div
      role="status"
      className={`flex items-center justify-between gap-3 rounded-md border px-3 py-2 text-sm ${
        variant === 'success'
          ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
          : 'border-red-200 bg-red-50 text-red-800'
      }`}
    >
      <span>{message}</span>
      <button type="button" className="rounded border px-2 py-0.5 text-xs" onClick={onClose}>
        close
      </button>
    </div>
  );
}

export default Toast;
