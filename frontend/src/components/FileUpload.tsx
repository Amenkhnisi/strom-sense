
import { useState, useRef } from "react";
import { FileUp, ImagePlus, X } from "lucide-react";
import { Toaster, toast } from "sonner";


interface FileUploadProps {
    onFileSelect: (file: File) => void;

}

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect }) => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const validTypes = ["application/pdf", "image/jpeg", "image/png"];

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file && validTypes.includes(file.type)) {
            setSelectedFile(file);
            onFileSelect(file);
            toast.success("File uploaded successfully!");

            if (file.type.startsWith("image")) {
                const reader = new FileReader();
                reader.onloadend = () => setPreviewUrl(reader.result as string);
                reader.readAsDataURL(file);
            } else {
                setPreviewUrl(null);
            }
        } else {
            toast.error("Please upload a PDF, JPG, or PNG file.");
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file && validTypes.includes(file.type)) {
            setSelectedFile(file);
            onFileSelect(file);
            toast.success("File uploaded successfully!");

            if (file.type.startsWith("image")) {
                const reader = new FileReader();
                reader.onloadend = () => setPreviewUrl(reader.result as string);
                reader.readAsDataURL(file);
            } else {
                setPreviewUrl(null);
            }
        } else {
            toast.error("Invalid file type.");
        }
    };

    const handleClick = () => fileInputRef.current?.click()
    /*  const handleRemove = () => {
         setSelectedFile(null);
         setPreviewUrl(null);
         toast.success("File removed successfully!");
     }; */

    return (
        <div
            className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center cursor-pointer hover:border-green-500 transition-shadow animate-fade-in"
            onClick={handleClick}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
        >
            <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
            />
            <Toaster richColors position="top-right" />
            {selectedFile ? (
                <div className="flex flex-col items-center space-y-3">
                    {previewUrl ? (
                        <img
                            src={previewUrl}
                            alt="Preview"
                            className="max-h-48 rounded-md shadow-md"
                        />
                    ) : (
                        <FileUp className="w-8 h-8 text-green-600" />
                    )}
                    <p className="text-sm text-gray-700 font-medium">
                        {selectedFile.name}
                    </p>
                    <button
                        type="button"
                        className="flex items-center gap-1 text-red-500 hover:text-red-600 text-sm"
                    >
                        <X className="w-4 h-4" />
                        Remove file
                    </button>
                </div>
            ) : (
                <div className="flex flex-col items-center space-y-2 text-gray-500">
                    <ImagePlus className="w-8 h-8 text-green-500" />
                    <p className="text-sm">Drag & drop your bill here</p>
                    <p className="text-xs">or click to upload PDF or image</p>
                </div>
            )}
        </div>
    );
};

export default FileUpload;
