'use client';

/**
 * Header Component
 *
 * Top navigation bar with breadcrumbs, search, and user menu
 */

import * as React from 'react';
import { Menu, Search, Bell, User, LogOut } from 'lucide-react';
import { ThemeToggle } from './theme-toggle';
import { useAuth } from '../contexts/auth-context';
import { cn } from '../utils/cn';
import type { BreadcrumbItem } from '../types';

interface HeaderProps {
  onMenuClick?: () => void;
  breadcrumbs?: BreadcrumbItem[];
}

export function Header({ onMenuClick, breadcrumbs = [] }: HeaderProps) {
  const [showUserMenu, setShowUserMenu] = React.useState(false);
  const [showNotifications, setShowNotifications] = React.useState(false);
  const { user, logout } = useAuth();

  const handleLogout = () => {
    setShowUserMenu(false);
    logout();
  };

  return (
    <header className="h-16 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950">
      <div className="h-full px-4 flex items-center justify-between">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          {/* Mobile Menu Button */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="Toggle menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Breadcrumbs */}
          {breadcrumbs.length > 0 && (
            <nav className="hidden md:flex items-center gap-2 text-sm">
              {breadcrumbs.map((item, index) => (
                <React.Fragment key={index}>
                  {index > 0 && (
                    <span className="text-gray-400 dark:text-gray-600">/</span>
                  )}
                  {item.href ? (
                    <a
                      href={item.href}
                      className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
                    >
                      {item.title}
                    </a>
                  ) : (
                    <span className="text-gray-900 dark:text-gray-100 font-medium">
                      {item.title}
                    </span>
                  )}
                </React.Fragment>
              ))}
            </nav>
          )}
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="hidden md:flex relative">
            <input
              type="text"
              placeholder="Search..."
              className={cn(
                'w-64 px-4 py-2 pl-10 rounded-lg border',
                'bg-gray-50 dark:bg-gray-900',
                'border-gray-200 dark:border-gray-800',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600',
                'text-sm'
              )}
            />
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          </div>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 relative"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5 text-gray-600 dark:text-gray-300" />
              <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
            </button>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-800 z-50">
                <div className="p-4 border-b border-gray-200 dark:border-gray-800">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                    Notifications
                  </h3>
                </div>
                <div className="p-4 text-sm text-gray-600 dark:text-gray-400">
                  No new notifications
                </div>
              </div>
            )}
          </div>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label="User menu"
            >
              <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
                <span className="text-white font-semibold text-sm">
                  {user?.name?.charAt(0).toUpperCase() || 'A'}
                </span>
              </div>
              <div className="hidden md:block text-left">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {user?.name || 'Admin User'}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {user?.email || 'admin@trademate.com'}
                </div>
              </div>
            </button>

            {/* User Dropdown */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-800 z-50">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {user?.name || 'Admin User'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {user?.email}
                  </p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center gap-2 text-red-600 dark:text-red-400 rounded-b-lg"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
