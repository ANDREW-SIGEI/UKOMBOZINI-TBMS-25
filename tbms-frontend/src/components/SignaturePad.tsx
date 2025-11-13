import { useRef, useState, useEffect } from 'react';
import { toast } from 'react-toastify';

interface SignaturePadProps {
  onSignature: (signatureData: string) => void;
  label: string;
  currentSignature?: string;
}

const SignaturePad = ({ onSignature, label, currentSignature }: SignaturePadProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [signature, setSignature] = useState<string | null>(currentSignature || null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    context.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Set drawing properties
    context.lineWidth = 2;
    context.lineCap = 'round';
    context.strokeStyle = '#000000';

    // Clear canvas
    context.clearRect(0, 0, canvas.width, canvas.height);
  }, []);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    setIsDrawing(true);
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    context.beginPath();
    context.moveTo(x, y);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    context.lineTo(x, y);
    context.stroke();
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setIsDrawing(false);

    const canvas = canvasRef.current;
    if (!canvas) return;

    const signatureData = canvas.toDataURL('image/png');
    setSignature(signatureData);
    onSignature(signatureData);
  };

  const clearSignature = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    context.clearRect(0, 0, canvas.width, canvas.height);
    setSignature(null);
    onSignature('');
  };

  const isCanvasEmpty = () => {
    const canvas = canvasRef.current;
    if (!canvas) return true;

    const context = canvas.getContext('2d');
    if (!context) return true;

    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    return imageData.data.every(pixel => pixel === 0);
  };

  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-gray-700">
        {label}
      </label>

      <div className="border border-gray-300 rounded-lg p-4">
        {signature ? (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <img
                src={signature}
                alt="Signature"
                className="max-w-full h-auto border border-gray-200 rounded"
              />
            </div>
            <div className="flex justify-center space-x-2">
              <button
                type="button"
                onClick={clearSignature}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Clear & Sign Again
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="relative bg-white border-2 border-gray-200 rounded-lg">
              <canvas
                ref={canvasRef}
                width={400}
                height={200}
                className="w-full h-48 cursor-crosshair border border-gray-200 rounded"
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
              />
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                {!isCanvasEmpty() ? null : (
                  <p className="text-gray-400 text-sm">
                    Sign here with your mouse or touch
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-center space-x-2">
              <button
                type="button"
                onClick={clearSignature}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Clear
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SignaturePad;
