import { FileSpreadsheet, FileText, Presentation } from "lucide-react";
import type { ElementType } from "react";

export interface FileTypeConfig {
  icon: ElementType;
  label: string;
  bg: string;
  iconColor: string;
}

export const FILE_TYPE_CONFIG: Record<string, FileTypeConfig> = {
  pdf: {
    icon: FileText,
    label: "PDF Document",
    bg: "bg-red-100 dark:bg-red-900/30",
    iconColor: "text-red-600 dark:text-red-400",
  },
  docx: {
    icon: FileText,
    label: "Word Document",
    bg: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
  },
  pptx: {
    icon: Presentation,
    label: "PowerPoint",
    bg: "bg-orange-100 dark:bg-orange-900/30",
    iconColor: "text-orange-600 dark:text-orange-400",
  },
  xlsx: {
    icon: FileSpreadsheet,
    label: "Excel Spreadsheet",
    bg: "bg-green-100 dark:bg-green-900/30",
    iconColor: "text-green-600 dark:text-green-400",
  },
  xls: {
    icon: FileSpreadsheet,
    label: "Excel Spreadsheet",
    bg: "bg-green-100 dark:bg-green-900/30",
    iconColor: "text-green-600 dark:text-green-400",
  },
};

export const DEFAULT_FILE_CONFIG: FileTypeConfig = {
  icon: FileText,
  label: "Document",
  bg: "bg-zinc-100 dark:bg-zinc-700",
  iconColor: "text-zinc-500 dark:text-zinc-400",
};
