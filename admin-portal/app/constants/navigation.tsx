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
  Workflow,
  TrendingUp,
  GitBranch,
  Search,
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
    title: 'Data Pipeline',
    href: '/data-pipeline',
    icon: Workflow,
    children: [
      {
        title: 'Overview',
        href: '/data-pipeline',
        icon: LayoutDashboard,
      },
      {
        title: 'Documents',
        href: '/data-pipeline/documents',
        icon: FileText,
      },
      {
        title: 'Research',
        href: '/data-pipeline/research',
        icon: TrendingUp,
      },
    ],
  },
  {
    title: 'Knowledge Graph',
    href: '/knowledge-graph',
    icon: GitBranch,
    children: [
      {
        title: 'Overview',
        href: '/knowledge-graph',
        icon: LayoutDashboard,
      },
      {
        title: 'Ingestion',
        href: '/knowledge-graph/ingest',
        icon: Database,
      },
      {
        title: 'Query',
        href: '/knowledge-graph/query',
        icon: Search,
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
