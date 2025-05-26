"use client"

import type React from "react"
import { useState, useCallback, CSSProperties } from "react"
import SyntaxHighlighter from 'react-syntax-highlighter';
import { Button } from "@/components/ui/button"
import { Copy, Check } from "lucide-react"

interface CodeBlockProps {
  className?: string
  children: React.ReactNode
  theme?: { [key: string]: CSSProperties; } | undefined
}

const CodeBlock = ({ className, children, theme }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false)

  // Extract language from className (format: "language-xxx" or "lang-xxx")
  const match = /(?:language-|lang-)(\w+)/.exec(className || "")
  const language = match ? match[1] : "text"

  const codeString = String(children).replace(/\n$/, "")

  const copyToClipboard = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(codeString)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy text: ", err)
    }
  }, [codeString])

  return (
    <div className="code-block-wrapper relative rounded-lg border bg-muted/50">
      {/* Header with language tag and copy button */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30 rounded-t-lg">
        <div className="flex items-center gap-2">
          {language && (
            <span className="text-xs font-medium text-muted-foreground bg-background px-2 py-1 rounded">
              {language}
            </span>
          )}
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={copyToClipboard}
          className="size-6 p-0 hover:bg-background"
          title={copied ? "Copied!" : "Copy code"}
        >
          {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>

      {/* Code content with horizontal scroll */}
      <div className="relative overflow-x-auto  scrollbar-thin scrollbar-thumb-red-500 scrollbar-track-transparent hover:scrollbar-thumb-blue-500">
        <SyntaxHighlighter
          language={language}
          style={theme}
          customStyle={{
            margin: 0,
            borderRadius: "0 0 8px 8px",
            background: "transparent",
            padding: "1rem",
          }}
          codeTagProps={{
            style: {
              fontSize: "0.875rem",
              fontFamily:
                'ui-monospace, SFMono-Regular, "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
            },
          }}
        >
          {codeString}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}

export default CodeBlock
