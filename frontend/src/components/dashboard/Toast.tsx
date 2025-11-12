interface ToastProps {
  type: 'success' | 'error' | 'info';
  message: string;
  onClose: () => void;
}

const colorMap = {
  success: 'bg-green-50 text-green-700 border-green-200',
  error: 'bg-red-50 text-red-700 border-red-200',
  info: 'bg-blue-50 text-blue-700 border-blue-200',
};

export function Toast({ type, message, onClose }: ToastProps) {
  return (
    <div className={`pointer-events-auto border px-4 py-3 rounded-lg shadow ${colorMap[type]}`}>
      <div className="flex items-start gap-3">
        <span className="flex-1 text-sm">{message}</span>
        <button onClick={onClose} className="text-xs text-current underline">
          关闭
        </button>
      </div>
    </div>
  );
}

export default Toast;