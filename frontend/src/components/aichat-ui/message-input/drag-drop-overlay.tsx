import { Paperclip } from "lucide-react"

export function DragDropOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-blue-50/90 dark:bg-blue-900/30 backdrop-blur-[1px] z-10">
      <div className="flex flex-col items-center gap-2 text-blue-600 dark:text-blue-400">
        <Paperclip className="h-8 w-8" />
        <p className="font-medium">Drop files to upload</p>
      </div>
    </div>
  )
}
