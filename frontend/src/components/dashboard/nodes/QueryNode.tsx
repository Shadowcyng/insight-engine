// src/components/dashboard/nodes/QueryNode.tsx
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Handle, Position, type NodeTypes } from "@xyflow/react";
import { Send, Database, Lock } from "lucide-react";
import { useStore } from "@nanostores/react";
import { $socket } from "@/api/wsClient";

export function QueryNode({ data }: any) {
  const isLinked = !!data.upload_id;
  const [input, setInput] = useState("");
  const socket = useStore($socket);

  const onSend = () => {
    if (!socket || !input.trim()) return;
    // Minor comment: This matches the 'action' logic in your backend websocket.py
    socket.send(
      JSON.stringify({
        action: "user_query",
        upload_id: data.upload_id,
        question: input,
      }),
    );
    setInput("");
  };

  return (
    <div
      className={`w-80 shadow-2xl rounded-xl bg-slate-900 border border-slate-700 overflow-hidden ${
        isLinked
          ? "bg-slate-900 border-blue-500/50"
          : "bg-slate-950 border-slate-800 opacity-75"
      }`}
    >
      <div className="bg-slate-800 px-3 py-2 flex items-center gap-2 border-b border-slate-700">
        {isLinked ? (
          <Database size={14} className="text-blue-400" />
        ) : (
          <Lock size={14} className="text-slate-500" />
        )}{" "}
        <span className="text-[10px] font-bold text-slate-400 uppercase">
          {isLinked ? "Query Engine" : "Link a File to Start"}
        </span>
      </div>
      <div className="p-3 space-y-3">
        {/* Result Area */}
        {data.answer && (
          <div className="p-2 bg-black/40 rounded border border-white/5 text-[11px] text-slate-300 max-h-40 overflow-y-auto prose prose-invert prose-p:leading-relaxed">
            <ReactMarkdown>{data.answer}</ReactMarkdown>
          </div>
        )}

        {/* Input Area */}
        <div className="flex gap-2">
          <input
            className="flex-1 bg-slate-950 border border-slate-800 rounded px-2 py-1 text-[11px] text-white focus:outline-none focus:border-blue-500"
            placeholder={
              isLinked ? "Ask about your data..." : "Connection required..."
            }
            disabled={!isLinked}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSend()}
          />
          <button
            onClick={onSend}
            disabled={!isLinked}
            className="p-1 bg-blue-600 rounded hover:bg-blue-500 transition-colors"
          >
            <Send size={12} className="text-white" />
          </button>
        </div>
      </div>

      <Handle type="target" position={Position.Left} className="bg-blue-500" />
      <Handle type="source" position={Position.Right} className="bg-blue-500" />
    </div>
  );
}
