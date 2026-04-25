const API_BASE = process.env.NEXT_PUBLIC_SERVER_URL ?? "http://localhost:8000";

export interface UploadResult {
  filename: string;
  file_type: string;
  text: string;
  char_count: number;
}

const UploadService = {
  uploadDocument: async (file: File, token: string): Promise<UploadResult> => {
    const form = new FormData();
    form.append("file", file);

    const res = await fetch(`${API_BASE}/v1/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail ?? "Upload failed");
    }

    return res.json() as Promise<UploadResult>;
  },
};

export default UploadService;
