import HealthBadge from "@/components/HealthBadge";
import IngestDashboard from "@/components/IngestDashboard";

export default function Page() {
  return (
    <div className="flex flex-1 flex-col">
      {/* Top nav */}
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              TradeMate
            </h1>
            <p className="text-xs text-zinc-500">Document Ingestion Pipeline</p>
          </div>
          <HealthBadge />
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-8">
        <IngestDashboard />
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-200 dark:border-zinc-800">
        <div className="mx-auto max-w-3xl px-6 py-4">
          <p className="text-xs text-zinc-400">
            Documents are ingested via S3 → parsed → chunked → embedded with{" "}
            <code className="font-mono">text-embedding-3-large</code> → upserted
            to Pinecone.
          </p>
        </div>
      </footer>
    </div>
  );
}
