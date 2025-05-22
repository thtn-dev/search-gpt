"use client";

import type React from "react";

import { useState, useRef, type FormEvent } from "react";
import { FileList } from "./file-list";
import { MessageTextarea } from "./message-textarea";
import { AttachButton } from "./attach-button";
import { SendButton } from "./send-button";
import { DragDropOverlay } from "./drag-drop-overlay";
import { cn } from "@/lib/utils";

interface MessageInputProps {
  onSendMessage: (message: string, files: File[]) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function MessageInput({
  onSendMessage,
  placeholder = "Ask me anything...",
  disabled = false,
  className,
}: MessageInputProps) {
  const [message, setMessage] = useState<string>("");
  const [files, setFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [dragCounter, setDragCounter] = useState<number>(0);
  const isDraggingOver = dragCounter > 0;

  const handleAddFiles = (newFiles: File[]) => {
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const handleRemoveFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    if (message.trim() || files.length > 0) {
      onSendMessage(message, files);
      setMessage("");
      setFiles([]);

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent<HTMLFormElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter((prev) => prev + 1);
  };

  const handleDragOver = (e: React.DragEvent<HTMLFormElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e: React.DragEvent<HTMLFormElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter((prev) => Math.max(0, prev - 1));
  };

  const handleDrop = (e: React.DragEvent<HTMLFormElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter(0);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      handleAddFiles(newFiles);
    }
  };

  return (
    <div className={cn("w-full max-w-4xl p-5 mx-auto ", className)}>
      {files.length > 0 && (
        <FileList files={files} onRemoveFile={handleRemoveFile} />
      )}

      <form
        onSubmit={handleSubmit}
        className={cn(
          "h-auto flex flex-col gap-0 border  border-gray-200 dark:border-gray-700 rounded-2xl p-2 bg-white dark:bg-gray-800 relative transition duration-200 ease-in-out hover:shadow-md",
          isDraggingOver &&
            "border-blue-500 border-dashed bg-blue-50 dark:bg-blue-900/20"
        )}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <MessageTextarea
          ref={textareaRef}
          value={message}
          onChange={setMessage}
          placeholder={placeholder}
          disabled={disabled}
          onEnterSubmit={handleSubmit}
        />
        <div className="flex items-center justify-between">
          <AttachButton
            disabled={disabled}
            fileInputRef={fileInputRef}
            onFilesSelected={handleAddFiles}
          />
          <SendButton
            disabled={disabled || (message.trim() === "" && files.length === 0)}
          />
        </div>

        {isDraggingOver && <DragDropOverlay />}
      </form>
    </div>
  );
}
