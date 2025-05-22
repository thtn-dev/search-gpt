"use client"

import type React from "react"

import { forwardRef, type ChangeEvent, type FormEvent } from "react"
import { cn } from "@/lib/utils"

interface MessageTextareaProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  onEnterSubmit: (e: FormEvent) => void
  className?: string
}

export const MessageTextarea = forwardRef<HTMLTextAreaElement, MessageTextareaProps>(
  ({ value, onChange, placeholder, disabled, onEnterSubmit, className }, ref) => {
    const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value)

      // Auto-resize textarea
      const textarea = e.target
      textarea.style.height = "auto"
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        onEnterSubmit(e)
      }
    }

    return (
      <div className="relative flex-1 flex items-center">
        <textarea
          ref={ref}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className={cn(
            "w-full resize-none bg-transparent py-2 px-2 focus:outline-none focus:ring-0 dark:text-gray-100",
            className,
          )}
          style={{ maxHeight: "200px", overflowY: "auto" }}
        />
      </div>
    )
  },
)

MessageTextarea.displayName = "MessageTextarea"
