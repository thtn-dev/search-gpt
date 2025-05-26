import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Send } from 'lucide-react';

interface SendButtonProps {
  disabled?: boolean;
  className?: string;
}

export function SendButton({ disabled = false, className }: SendButtonProps) {
  return (
    <Button
      type='submit'
      size='icon'
      className={cn('h-8 w-8 shrink-0', className)}
      disabled={disabled}
    >
      <Send className='h-4 w-4' />
      <span className='sr-only'>Send message</span>
    </Button>
  );
}
