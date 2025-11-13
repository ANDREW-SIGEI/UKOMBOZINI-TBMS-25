import { useRef, useState, useCallback } from 'react';
import { toast } from 'react-toastify';

interface CameraCaptureProps {
  onCapture: (imageData: string) => void;
  label: string;
  currentImage?: string;
}

const CameraCapture = ({ onCapture, label, currentImage }: CameraCaptureProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(currentImage || null);
  const streamRef = useRef<MediaStream | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setIsStreaming(true);
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      toast.error('Unable to access camera. Please check permissions.');
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const captureImage = useCallback(() => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');

      if (context) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);

        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        setCapturedImage(imageData);
        onCapture(imageData);
        stopCamera();
        toast.success('Image captured successfully!');
      }
    }
  }, [onCapture, stopCamera]);

  const retakeImage = useCallback(() => {
    setCapturedImage(null);
    startCamera();
  }, [startCamera]);

  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-gray-700">
        {label}
      </label>

      <div className="border border-gray-300 rounded-lg p-4">
        {!capturedImage ? (
          <div className="space-y-4">
            <div className="relative bg-gray-100 rounded-lg overflow-hidden">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-64 object-cover"
                style={{ display: isStreaming ? 'block' : 'none' }}
              />
              <canvas
                ref={canvasRef}
                className="hidden"
              />

              {!isStreaming && (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  <div className="text-center">
                    <div className="text-4xl mb-2">📷</div>
                    <p>Camera preview will appear here</p>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-center space-x-2">
              {!isStreaming ? (
                <button
                  type="button"
                  onClick={startCamera}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Start Camera
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={captureImage}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    Capture
                  </button>
                  <button
                    type="button"
                    onClick={stopCamera}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    Stop Camera
                  </button>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="relative">
              <img
                src={capturedImage}
                alt="Captured"
                className="w-full h-64 object-cover rounded-lg shadow-md"
              />
            </div>

            <div className="flex justify-center space-x-2">
              <button
                type="button"
                onClick={retakeImage}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Retake
              </button>
              <button
                type="button"
                onClick={() => setCapturedImage(null)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Remove
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CameraCapture;
