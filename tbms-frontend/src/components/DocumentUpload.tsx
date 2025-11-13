import { useState, useRef } from 'react';
import { toast } from 'react-toastify';

interface DocumentUploadProps {
  onFileSelect: (file: File, preview: string) => void;
  accept?: string;
  maxSize?: number; // in MB
  label: string;
  currentPreview?: string;
}

const DocumentUpload = ({
  onFileSelect,
  accept = "image/*,.pdf",
  maxSize = 5,
  label,
  currentPreview
}: DocumentUploadProps) => {
  const [preview, setPreview] = useState<string | null>(currentPreview || null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    // Validate file size
    if (file.size > maxSize * 1024 * 1024) {
      toast.error(`File size must be less than ${maxSize}MB`);
      return;
    }

    // Create preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const previewUrl = e.target?.result as string;
        setPreview(previewUrl);
        onFileSelect(file, previewUrl);
      };
      reader.readAsDataURL(file);
    } else {
      // For non-image files, just pass the file
      setPreview(null);
      onFileSelect(file, '');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        {label}
      </label>

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileInputChange}
          className="hidden"
        />

        {preview ? (
          <div className="space-y-4">
            <img
              src={preview}
              alt="Document preview"
              className="max-w-full max-h-48 mx-auto rounded-lg shadow-md"
            />
            <p className="text-sm text-gray-600">
              Click to change document
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-4xl text-gray-400">
              📄
            </div>
            <div>
              <p className="text-sm text-gray-600">
                Drag and drop your document here, or{' '}
                <span className="text-blue-600 hover:text-blue-500">
                  browse
                </span>
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Supports: Images, PDF (Max {maxSize}MB)
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentUpload;
