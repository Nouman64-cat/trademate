'use client';

/**
 * Sidebar Navigation Component
 *
 * Responsive sidebar with collapsible sections and active state highlighting
 */

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { NAV_ITEMS } from '../constants/navigation';
import { cn } from '../utils/cn';
import type { NavItem } from '../types';

interface SidebarProps {
  collapsed?: boolean;
}

export function Sidebar({ collapsed = false }: SidebarProps) {
  const pathname = usePathname();
  const [expandedItems, setExpandedItems] = React.useState<string[]>([]);

  const toggleExpanded = (title: string) => {
    setExpandedItems((prev) =>
      prev.includes(title)
        ? prev.filter((item) => item !== title)
        : [...prev, title]
    );
  };

  const isActive = (href: string) => {
    return pathname === href || pathname.startsWith(href + '/');
  };

  const renderNavItem = (item: NavItem, level = 0) => {
    const Icon = item.icon;
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.title);
    const active = isActive(item.href);

    return (
      <div key={item.title} className="space-y-1">
        {hasChildren ? (
          <button
            onClick={() => toggleExpanded(item.title)}
            className={cn(
              'w-full flex items-center justify-between px-3 py-2 rounded-lg',
              'text-sm font-medium transition-colors duration-200',
              active
                ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800',
              collapsed && 'justify-center px-2'
            )}
          >
            <div className="flex items-center gap-3">
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && <span>{item.title}</span>}
            </div>
            {!collapsed && (
              <div>
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </div>
            )}
          </button>
        ) : (
          <Link
            href={item.href}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-lg',
              'text-sm font-medium transition-colors duration-200',
              active
                ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800',
              collapsed && 'justify-center px-2',
              level > 0 && 'pl-10'
            )}
          >
            <Icon className="h-5 w-5 flex-shrink-0" />
            {!collapsed && (
              <div className="flex items-center justify-between flex-1">
                <span>{item.title}</span>
                {item.badge !== undefined && (
                  <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                    {item.badge}
                  </span>
                )}
              </div>
            )}
          </Link>
        )}

        {/* Render children if expanded */}
        {hasChildren && isExpanded && !collapsed && (
          <div className="ml-3 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
            {item.children!.map((child) => renderNavItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside
      className={cn(
        'h-full border-r border-gray-200 dark:border-gray-800',
        'bg-white dark:bg-gray-950',
        'transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-gray-200 dark:border-gray-800 px-4">
        {collapsed ? (
          <span className="text-2xl font-bold text-blue-600">T</span>
        ) : (
          <span className="text-xl font-bold text-blue-600">TradeMate Admin</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-2 overflow-y-auto h-[calc(100%-4rem)]">
        {NAV_ITEMS.map((item) => renderNavItem(item))}
      </nav>
    </aside>
  );
}
