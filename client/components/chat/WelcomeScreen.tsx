import { TrendingUp, BarChart2, Globe, BookOpen } from "lucide-react";
import { cn } from "@/lib/cn";

interface Prompt {
  icon: React.ReactNode;
  label: string;
  prompt: string;
}

const SUGGESTED_PROMPTS: Prompt[] = [
  {
    icon: <Globe size={16} />,
    label: "Trade Overview",
    prompt: "Give me an overview of US-Pakistan trade relations in 2024",
  },
  {
    icon: <TrendingUp size={16} />,
    label: "Export Analysis",
    prompt: "What are the major textile products Pakistan exports to the US?",
  },
  {
    icon: <BarChart2 size={16} />,
    label: "Import Data",
    prompt: "What are the main items Pakistan imports from the United States?",
  },
  {
    icon: <BookOpen size={16} />,
    label: "Economic Trends",
    prompt: "How have US-Pakistan trade volumes changed over the last 5 years?",
  },
];

interface WelcomeScreenProps {
  onPromptSelect: (prompt: string) => void;
}

export function WelcomeScreen({ onPromptSelect }: WelcomeScreenProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
      {/* Logo mark */}
      <div className="mb-6 h-14 w-14 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
        <TrendingUp size={26} className="text-white" />
      </div>

      <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50 mb-2 text-center">
        What can I help you with?
      </h1>
      <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-10 text-center max-w-sm">
        Your AI-powered trade advisor. Ask about US-Pakistan trade statistics,
        tariffs, news, or market trends.
      </p>

      {/* Suggested prompts */}
      <div className="grid grid-cols-2 gap-3 w-full max-w-lg">
        {SUGGESTED_PROMPTS.map((item) => (
          <button
            key={item.label}
            onClick={() => onPromptSelect(item.prompt)}
            className={cn(
              "flex items-start gap-3 p-4 rounded-xl text-left",
              "border border-zinc-200 dark:border-zinc-700/60",
              "bg-white dark:bg-zinc-800/50",
              "hover:border-violet-400/60 hover:bg-violet-50/50 dark:hover:bg-zinc-800",
              "transition-all duration-150 group"
            )}
          >
            <span className="mt-0.5 text-zinc-400 group-hover:text-violet-500 transition-colors flex-shrink-0">
              {item.icon}
            </span>
            <div>
              <div className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 mb-0.5">
                {item.label}
              </div>
              <div className="text-sm text-zinc-700 dark:text-zinc-300 leading-snug">
                {item.prompt}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
