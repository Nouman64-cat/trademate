'use client';

/**
 * Theme Provider - Light/Dark Mode Support
 *
 * Wraps the app with next-themes provider to enable
 * system-based and manual theme switching.
 */

import * as React from 'react';
import { ThemeProvider as NextThemesProvider } from 'next-themes';

type ThemeProviderProps = Parameters<typeof NextThemesProvider>[0];

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
}
