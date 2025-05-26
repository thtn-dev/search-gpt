'use client';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  X,
  FileText,
  ImageIcon,
  FileArchive,
  Film,
  Music,
  File
} from 'lucide-react';

interface FileItemProps {
  file: File;
  onRemove: () => void;
  className?: string;
}

export function FileItem({ file, onRemove, className }: FileItemProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 bg-accent px-3 py-2 rounded-md border transition-all hover:shadow-sm',
        className
      )}
    >
      <span className='text-zinc-500 dark:text-zinc-400'>
        {getFileIcon(file.name)}
      </span>
      <div className='flex flex-col'>
        <span className='text-sm font-medium truncate max-w-[150px]'>
          {file.name}
        </span>
        <span className='text-xs text-zinc-500 dark:text-zinc-400'>
          {formatFileSize(file.size)}
        </span>
      </div>
      <Button
        variant='ghost'
        size='icon'
        className='h-6 w-6 ml-1 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-300'
        onClick={onRemove}
      >
        <X className='h-3.5 w-3.5' />
        <span className='sr-only'>Remove file</span>
      </Button>
    </div>
  );
}

// Helper function to format file size
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return (
    Number.parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  );
}

// Helper function to get appropriate icon based on file type
export function getFileIcon(fileName: string) {
  const extension = fileName.split('.').pop()?.toLowerCase() || '';

  switch (extension) {
    case 'pdf':
    case 'doc':
    case 'docx':
    case 'txt':
      return <FileText className='h-4 w-4' />;
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'webp':
      return <ImageIcon className='h-4 w-4' />;
    case 'zip':
    case 'rar':
    case '7z':
      return <FileArchive className='h-4 w-4' />;
    case 'mp4':
    case 'avi':
    case 'mov':
    case 'webm':
      return <Film className='h-4 w-4' />;
    case 'mp3':
    case 'wav':
    case 'ogg':
      return <Music className='h-4 w-4' />;
    default:
      return <File className='h-4 w-4' />;
  }
}
