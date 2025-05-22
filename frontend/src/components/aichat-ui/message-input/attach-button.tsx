"use client"

import { useRef, type ChangeEvent, type RefObject } from "react"
import { Paperclip } from "lucide-react"
import { Button } from "@/components/ui/button"

interface AttachButtonProps {
  disabled?: boolean
  fileInputRef?: RefObject<HTMLInputElement | null>
  onFilesSelected: (files: File[]) => void
}

export function AttachButton({
  disabled = false,
  fileInputRef: externalRef,
  onFilesSelected,
}: AttachButtonProps) {
  // Use provided ref or create our own if none is provided
  const internalRef = useRef<HTMLInputElement>(null)
  const fileInputRef = externalRef || internalRef

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      onFilesSelected(newFiles)
    }
  }

  return (
    <div className="relative">
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="h-9 w-9 shrink-0 rounded-full text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:bg-gray-800 transition-colors"
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
        accept="image/*,.pdf,.doc,.docx,.txt,.zip,.rar,.mp4,.mp3"
      />
    </div>
  )
}
