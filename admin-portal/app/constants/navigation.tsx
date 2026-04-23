/**
 * Navigation Configuration
 */

import {
  LayoutDashboard,
  Users,
  MessageSquare,
  Settings,
  BarChart3,
  Database,
  Shield,
  FileText,
} from 'lucide-react';
import { NavItem } from '../types';

export const NAV_ITEMS: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'User Management',
    href: '/users',
    icon: Users,
  },
  {
    title: 'Chatbot Config',
    href: '/chatbot',
    icon: MessageSquare,
    children: [
      {
        title: 'Configuration',
        href: '/chatbot/config',
        icon: Settings,
      },
      {
        title: 'Tools',
        href: '/chatbot/tools',
        icon: Database,
      },
      {
        title: 'Prompts',
        href: '/chatbot/prompts',
        icon: FileText,
      },
    ],
  },
  {
    title: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
    children: [
      {
        title: 'General',
        href: '/settings/general',
        icon: Settings,
      },
      {
        title: 'Security',
        href: '/settings/security',
        icon: Shield,
      },
    ],
  },
];
