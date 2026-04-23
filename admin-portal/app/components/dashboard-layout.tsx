'use client';

/**
 * Dashboard Layout Component
 *
 * Main layout wrapper for all dashboard pages with sidebar and header
 */

import * as React from 'react';
import { Sidebar } from './sidebar';
import { Header } from './header';
import { ProtectedRoute } from './protected-route';
import type { BreadcrumbItem } from '../types';

interface DashboardLayoutProps {
  children: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
}

export function DashboardLayout({ children, breadcrumbs }: DashboardLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false);

  return (
    <ProtectedRoute>
    <div className="h-screen flex overflow-hidden bg-gray-50 dark:bg-gray-900">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar collapsed={sidebarCollapsed} />
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileSidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 z-50 lg:hidden">
            <Sidebar collapsed={false} />
          </div>
        </>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          onMenuClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
          breadcrumbs={breadcrumbs}
        />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
    </ProtectedRoute>
  );
}
