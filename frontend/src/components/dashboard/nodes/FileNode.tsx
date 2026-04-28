// src/components/dashboard/nodes/FileNode.tsx
import React, { useState, useRef } from "react";
import { Handle, Position } from "@xyflow/react";
import { UploadCloud, CheckCircle2, Loader2, BookOpen, X } from "lucide-react";
import { uploadFile } from "@/api/uploadApi"; // Your existing upload service
import { $nodes } from "@/store/canvasStore";

export function FileNode({ id, data }: any) {
  const [dragActive, setDragActive] = useState(false);
  const [status, setStatus] = useState(data.status || "idle");
  const [showFullSummary, setShowFullSummary] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
    setStatus("uploading");
    try {
      const response = await uploadFile(file); // Should return { id: number, file_path: string }

      // Update this specific node in the store
      const currentNodes = $nodes.get();
      $nodes.set(
        currentNodes.map((n) =>
          n.id === id
            ? {
                ...n,
                data: {
                  ...n.data,
                  upload_id: response.id,
                  filename: file.name,
                  status: "ready",
                },
              }
            : n,
        ),
      );

      setStatus("ready");
    } catch (err) {
      setStatus("idle");
      console.error("Upload failed", err);
    }
  };

  // Drag & Drop Handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className={`w-64 p-4 rounded-xl border-2 border-dashed transition-all bg-slate-900 ${
        dragActive ? "border-indigo-500 bg-indigo-500/10" : "border-slate-700"
      }`}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
        className="hidden"
        accept=".csv"
      />

      <div className="flex flex-col items-center justify-center gap-3 py-2 text-center">
        {status === "idle" && (
          <>
            <UploadCloud size={32} className="text-slate-500" />
            <div>
              <p className="text-[11px] font-bold text-slate-300 uppercase">
                Upload CSV
              </p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                className="text-[10px] text-indigo-400 hover:underline"
              >
                or browse files
              </button>
            </div>
          </>
        )}

        {status === "uploading" && (
          <>
            <Loader2 size={32} className="text-indigo-500 animate-spin" />
            <p className="text-[10px] font-bold text-slate-400 uppercase">
              Processing...
            </p>
          </>
        )}

        {status === "ready" && (
          <>
            <div className="p-2 bg-emerald-500/20 rounded-full">
              <CheckCircle2 size={24} className="text-emerald-400" />
            </div>
            <div className="overflow-hidden w-full">
              <p className="text-[11px] font-bold text-emerald-400 uppercase">
                Ready
              </p>
              <p className="text-[10px] text-slate-400 truncate">
                {data.filename}
              </p>
            </div>
            {data.ai_summary && (
              <div className="mt-3 p-2 bg-indigo-500/10 border border-indigo-500/20 rounded">
                <p className="text-[9px] font-bold text-indigo-400 uppercase mb-1">
                  AI Summary
                </p>
                <p className="text-[10px] text-slate-300 line-clamp-2 italic leading-relaxed">
                  {data.ai_summary}
                </p>
                <button
                  onClick={() => setShowFullSummary(true)}
                  className="nodrag text-[10px] text-indigo-400 mt-1 hover:text-indigo-300 transition-colors font-medium flex items-center gap-1"
                >
                  <BookOpen size={10} /> Read full insight
                </button>
              </div>
            )}

            {/* Expanded Summary Overlay */}
            {showFullSummary && (
              <div className="absolute inset-0 bg-slate-900 rounded-xl p-4 border-2 border-indigo-500 shadow-2xl flex flex-col">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold text-indigo-400 uppercase">
                    Full Dataset Insight
                  </span>
                  <button
                    onClick={() => setShowFullSummary(false)}
                    className="text-slate-500 hover:text-white"
                  >
                    <X size={14} />
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto text-[11px] text-slate-300 leading-relaxed pr-1 scrollbar-thin scrollbar-thumb-slate-700">
                  {data.ai_summary}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-indigo-500"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-indigo-500"
      />
    </div>
  );
}
