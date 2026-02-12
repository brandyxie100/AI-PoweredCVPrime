/**
 * FileUpload component — drag-and-drop or click-to-browse file upload.
 *
 * Uses react-dropzone for a polished drag-and-drop experience.
 *
 * Author: brandyxie
 * Email:  brandyxie100@qq.com
 */

"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface FileUploadProps {
  onFileSelected: (file: File) => void;
  isUploading: boolean;
}

export default function FileUpload({
  onFileSelected,
  isUploading,
}: FileUploadProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelected(acceptedFiles[0]);
      }
    },
    [onFileSelected]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
    disabled: isUploading,
  });

  return (
    <div className="mx-auto max-w-2xl">
      <div
        {...getRootProps()}
        className={`
          cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center
          transition-all duration-200
          ${
            isDragActive
              ? "border-primary-400 bg-primary-50"
              : "border-gray-300 bg-white hover:border-primary-300 hover:bg-gray-50"
          }
          ${isUploading ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        <input {...getInputProps()} />

        {/* Upload icon */}
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-100">
          <svg
            className="h-8 w-8 text-primary-600"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
        </div>

        {isUploading ? (
          <div>
            <p className="text-lg font-semibold text-gray-700">
              Uploading...
            </p>
            <div className="mt-3 mx-auto h-2 w-48 overflow-hidden rounded-full bg-gray-200">
              <div className="h-full animate-pulse rounded-full bg-primary-500 w-3/4" />
            </div>
          </div>
        ) : isDragActive ? (
          <p className="text-lg font-semibold text-primary-600">
            Drop your CV here...
          </p>
        ) : (
          <div>
            <p className="text-lg font-semibold text-gray-700">
              Drag &amp; drop your CV here
            </p>
            <p className="mt-1 text-sm text-gray-500">
              or{" "}
              <span className="font-medium text-primary-600">
                click to browse
              </span>
            </p>
            <p className="mt-3 text-xs text-gray-400">
              Supports PDF, DOCX, and TXT files
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
