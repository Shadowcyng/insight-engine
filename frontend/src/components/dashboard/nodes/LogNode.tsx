// src/components/dashboard/nodes/LogNode.tsx
import { useStore } from "@nanostores/react";
import { $agentLogs } from "@/store/logStore";
import { Terminal } from "lucide-react";
import { Handle, Position } from "@xyflow/react";

const LogColorMap: Record<string, string> = {
  info: "text-indigo-300",
  success: "text-emerald-400",
  error: "text-red-400",
  log: "text-blue-300",
  query: "text-amber-300",
};

export function LogNode() {
  const logs = useStore($agentLogs);

  return (
    <div className="w-100 h-64 shadow-2xl rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
      {/* Minor comment: Node Header */}
      <div className="bg-slate-900 px-3 py-2 flex items-center gap-2 border-b border-slate-800">
        <Terminal size={14} className="text-indigo-400" />
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
          Agent Execution Log
        </span>
      </div>

      {/* Minor comment: Terminal Body */}
      <div className="p-3 h-52 overflow-y-auto font-mono text-[10px] space-y-1 bg-black/40">
        {logs.length === 0 && (
          <p className="text-slate-600 italic">Waiting for agent signal...</p>
        )}
        {logs.map((log) => (
          <div key={log.id} className="flex gap-2">
            <span className="text-slate-600">[{log.timestamp}]</span>
            <span className={LogColorMap[log.type]}>{log.message}</span>
          </div>
        ))}
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="w-2 h-2 bg-slate-700 border-none"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-2 h-2 bg-slate-700 border-none"
      />
    </div>
  );
}
