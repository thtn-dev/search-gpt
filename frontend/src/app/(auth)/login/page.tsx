'use client';

import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { signIn } from 'next-auth/react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';

const formSchema = z.object({
  email: z.string(),
  password: z.string().min(8, 'Password must be at least 8 characters long')
});

const Login05Page = () => {
  const router = useRouter();
  const params = useSearchParams();

  const callbackUrl = params.get('callbackUrl') || '/';

  const form = useForm<z.infer<typeof formSchema>>({
    defaultValues: {
      email: '',
      password: ''
    },
    resolver: zodResolver(formSchema)
  });

  const onSubmit = async (data: z.infer<typeof formSchema>) => {
    console.log(data);
    const result = await signIn('credentials', {
      email: data.email,
      password: data.password,
      redirect: false,
      callbackUrl: callbackUrl
    });
    if (result?.error) {
      console.error(result.error);
    } else {
      router.push(result?.url || '/');
    }
  };

  return (
    <div className='h-screen flex items-center justify-center'>
      <div className='w-full h-full grid lg:grid-cols-2 p-4'>
        <div className='max-w-xs m-auto w-full flex flex-col items-center'>
          <p className='mt-4 text-xl font-bold tracking-tight'>
            Log in to Search AI
          </p>

          <div className='mt-8 flex items-center gap-3'>
            <Button
              variant='outline'
              size='icon'
              className='rounded-full h-10 w-10'
              onClick={() => signIn('google')}
            >
              <Image
                src={'/icons/google.svg'}
                alt='Google'
                width={18}
                height={18}
                className='!h-[18px] !w-[18px]'
              />
            </Button>
            <Button
              variant='outline'
              size='icon'
              className='rounded-full h-10 w-10'
              onClick={() => signIn('github')}
            >
              <Image
                src={'/icons/github.svg'}
                alt='Github'
                width={18}
                height={18}
                className='!h-[18px] !w-[18px]'
              />
            </Button>
            <Button
              variant='outline'
              size='icon'
              className='rounded-full h-10 w-10'
              onClick={() => signIn('azure-ad')}
            >
              <Image
                src={'/icons/microsoft.svg'}
                alt='Azure AD'
                width={18}
                height={18}
                className='!h-[18px] !w-[18px]'
              />
            </Button>
          </div>

          <div className='my-7 w-full flex items-center justify-center overflow-hidden'>
            <Separator />
            <span className='text-sm px-2'>OR</span>
            <Separator />
          </div>

          <Form {...form}>
            <form
              className='w-full space-y-4'
              onSubmit={form.handleSubmit(onSubmit)}
            >
              <FormField
                control={form.control}
                name='email'
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Username</FormLabel>
                    <FormControl>
                      <Input
                        type='email'
                        placeholder='Email'
                        className='w-full'
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name='password'
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input
                        type='password'
                        placeholder='Password'
                        className='w-full'
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type='submit' className='mt-4 w-full'>
                Continue with Email
              </Button>
            </form>
          </Form>

          <div className='mt-5 space-y-5'>
            <Link
              href='/forgot-password'
              className='text-sm block underline text-muted-foreground text-center'
            >
              Forgot your password?
            </Link>
            <p className='text-sm text-center'>
              Don&apos;t have an account?
              <Link
                href='/register'
                className='ml-1 underline text-muted-foreground'
              >
                Create account
              </Link>
            </p>
          </div>
        </div>
        <div className='bg-muted/60 hidden lg:block rounded-lg'>
          <div className='relative w-full h-full'>
            <Image
              src='/images/login-illustration.webp'
              alt='Login Illustration'
              fill
              className='object-cover rounded-lg'
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login05Page;
