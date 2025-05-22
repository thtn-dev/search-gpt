"use client"

import type React from "react"

import { useState, useRef, type ChangeEvent, type FormEvent } from "react"
import { Paperclip, X, Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface MessageInputProps {
  onSendMessage: (message: string, files: File[]) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function MessageInput({
  onSendMessage,
  placeholder = "Message...",
  disabled = false,
  className,
}: MessageInputProps) {
  const [message, setMessage] = useState<string>("")
  const [files, setFiles] = useState<File[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
      setFiles((prev) => [...prev, ...newFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()

    if (message.trim() || files.length > 0) {
      onSendMessage(message, files)
      setMessage("")
      setFiles([])

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }
    }
  }

  const handleTextareaChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)

    // Auto-resize textarea
    const textarea = e.target
    textarea.style.height = "auto"
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className={cn("w-full max-w-3xl mx-auto", className)}>
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-1 bg-white dark:bg-gray-700 px-2 py-1 rounded border border-gray-200 dark:border-gray-600"
            >
              <span className="text-sm truncate max-w-[150px]">{file.name}</span>
              <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => removeFile(index)}>
                <X className="h-3 w-3" />
                <span className="sr-only">Remove file</span>
              </Button>
            </div>
          ))}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="flex items-end gap-2 border border-gray-200 dark:border-gray-700 rounded-lg p-2 bg-white dark:bg-gray-800"
      >
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
        >
          <Paperclip className="h-5 w-5" />
          <span className="sr-only">Attach files</span>
        </Button>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          multiple
          disabled={disabled}
        />

        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full resize-none bg-transparent py-2 px-2 focus:outline-none focus:ring-0 dark:text-gray-100"
            style={{ maxHeight: "200px", overflowY: "auto" }}
          />
        </div>

        <Button
          type="submit"
          size="icon"
          className="h-8 w-8 shrink-0"
          disabled={disabled || (message.trim() === "" && files.length === 0)}
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Send message</span>
        </Button>
      </form>
    </div>
  )
}
