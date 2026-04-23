'use client';

import * as React from 'react';
import { DashboardLayout } from '../../components/dashboard-layout';
import { 
  Save, 
  RefreshCw, 
  Loader2, 
  FileText, 
  Search,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock
} from 'lucide-react';
import { cn } from '../../utils/cn';
import type { Prompt, PromptListItem } from '../../types';
import api from '../../services/api';

export default function ChatbotPromptsPage() {
  const [prompts, setPrompts] = React.useState<PromptListItem[]>([]);
  const [selectedPrompt, setSelectedPrompt] = React.useState<Prompt | null>(null);
  const [loadingList, setLoadingList] = React.useState(true);
  const [loadingDetail, setLoadingDetail] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState('');

  React.useEffect(() => {
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    try {
      setLoadingList(true);
      setError(null);
      const data = await api.get<PromptListItem[]>('/v1/admin/chatbot/prompts');
      setPrompts(data);
      
      // Select first prompt by default if available
      if (data.length > 0 && !selectedPrompt) {
        fetchPromptDetail(data[0].id);
      }
    } catch (err: any) {
      console.error('Failed to fetch prompts:', err);
      setError(err.message || 'Failed to load prompts');
    } finally {
      setLoadingList(false);
    }
  };

  const fetchPromptDetail = async (id: number) => {
    try {
      setLoadingDetail(true);
      setError(null);
      const data = await api.get<Prompt>(`/v1/admin/chatbot/prompts/${id}`);
      setSelectedPrompt(data);
    } catch (err: any) {
      console.error('Failed to fetch prompt detail:', err);
      setError(err.message || 'Failed to load prompt details');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSave = async () => {
    if (!selectedPrompt) return;

    try {
      setSaving(true);
      setError(null);
      await api.put(`/v1/admin/chatbot/prompts/${selectedPrompt.id}`, {
        content: selectedPrompt.content,
        description: selectedPrompt.description,
        is_active: selectedPrompt.is_active,
      });
      
      // Update list item if name or description changed
      setPrompts(prev => prev.map(p => 
        p.id === selectedPrompt.id 
          ? { ...p, description: selectedPrompt.description, is_active: selectedPrompt.is_active, updated_at: new Date().toISOString() }
          : p
      ));
      
      alert('Prompt saved successfully!');
    } catch (err: any) {
      console.error('Failed to save prompt:', err);
      setError(err.message || 'Failed to save prompt');
    } finally {
      setSaving(false);
    }
  };

  const filteredPrompts = prompts.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <DashboardLayout
      breadcrumbs={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: 'Chatbot', href: '/chatbot' },
        { title: 'Prompts' },
      ]}
    >
      <div className="h-[calc(100vh-12rem)] flex flex-col gap-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              System Prompts
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Manage and tune the core instructions for the TradeMate AI
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={fetchPrompts}
              className="inline-flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <RefreshCw className={cn("h-4 w-4", loadingList && "animate-spin")} />
              Refresh
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !selectedPrompt}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="h-4 w-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        <div className="flex-1 flex gap-6 min-h-0">
          {/* Prompts List Sidebar */}
          <div className="w-80 flex flex-col bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search prompts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {loadingList ? (
                <div className="flex flex-col items-center justify-center h-32 gap-2">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                  <span className="text-xs text-gray-500">Loading prompts...</span>
                </div>
              ) : filteredPrompts.length === 0 ? (
                <div className="text-center p-8 text-gray-500 text-sm">
                  No prompts found
                </div>
              ) : (
                filteredPrompts.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => fetchPromptDetail(p.id)}
                    className={cn(
                      'w-full text-left p-3 rounded-lg transition-colors',
                      selectedPrompt?.id === p.id
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-100 dark:border-blue-800 shadow-sm'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <FileText className={cn(
                          "h-4 w-4",
                          selectedPrompt?.id === p.id ? "text-blue-600" : "text-gray-400"
                        )} />
                        <span className={cn(
                          "font-medium text-sm",
                          selectedPrompt?.id === p.id ? "text-blue-700 dark:text-blue-400" : "text-gray-900 dark:text-gray-100"
                        )}>
                          {p.name}
                        </span>
                      </div>
                      {p.is_active ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                      ) : (
                        <XCircle className="h-3.5 w-3.5 text-gray-400" />
                      )}
                    </div>
                    {p.description && (
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-1">
                        {p.description}
                      </p>
                    )}
                    <div className="mt-2 flex items-center gap-1 text-[10px] text-gray-400">
                      <Clock className="h-3 w-3" />
                      <span>Updated {new Date(p.updated_at).toLocaleDateString()}</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Prompt Editor Area */}
          <div className="flex-1 flex flex-col bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            {loadingDetail ? (
              <div className="flex-1 flex flex-col items-center justify-center gap-3">
                <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
                <p className="text-gray-500">Loading prompt content...</p>
              </div>
            ) : selectedPrompt ? (
              <div className="flex-1 flex flex-col min-h-0">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                      {selectedPrompt.name}
                    </h2>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Status:</span>
                      <button
                        onClick={() => setSelectedPrompt({...selectedPrompt, is_active: !selectedPrompt.is_active})}
                        className={cn(
                          "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider transition-colors",
                          selectedPrompt.is_active 
                            ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                            : "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
                        )}
                      >
                        {selectedPrompt.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="p-4 space-y-4 flex-1 flex flex-col min-h-0">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Description
                    </label>
                    <input
                      type="text"
                      value={selectedPrompt.description || ''}
                      onChange={(e) => setSelectedPrompt({...selectedPrompt, description: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="What is this prompt used for?"
                    />
                  </div>

                  <div className="flex-1 flex flex-col min-h-0">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Prompt Content
                    </label>
                    <textarea
                      value={selectedPrompt.content}
                      onChange={(e) => setSelectedPrompt({...selectedPrompt, content: e.target.value})}
                      className={cn(
                        "flex-1 w-full p-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg",
                        "font-mono text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-blue-500",
                        "resize-none overflow-y-auto"
                      )}
                      placeholder="Enter the system instructions here..."
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-gray-500 gap-4">
                <FileText className="h-16 w-16 opacity-20" />
                <p>Select a prompt from the list to view and edit its content</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
