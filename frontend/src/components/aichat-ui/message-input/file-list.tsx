import { cn } from "@/lib/utils"
import { FileItem } from "./file-item"

interface FileListProps {
  files: File[]
  onRemoveFile: (index: number) => void
  className?: string
}

export function FileList({ files, onRemoveFile, className }: FileListProps) {
  if (files.length === 0) return null

  return (
    <div
      className={cn(
        "flex flex-wrap gap-2 mb-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700",
        className,
      )}
    >
      {files.map((file, index) => (
        <FileItem key={index} file={file} onRemove={() => onRemoveFile(index)} />
      ))}
    </div>
  )
}
