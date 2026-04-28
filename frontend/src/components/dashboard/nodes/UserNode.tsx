// src/components/dashboard/nodes/UserNode.tsx
import { Handle, Position } from "@xyflow/react";
import { useStore } from "@nanostores/react";
import { $user } from "@/store/authStore";
import { User, ShieldCheck } from "lucide-react";

export function UserNode() {
  const user = useStore($user);

  return (
    <div className="px-4 py-3 shadow-2xl rounded-xl bg-slate-900 border border-indigo-500/50 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-indigo-500/20 rounded-lg">
          <User className="text-indigo-400" size={20} />
        </div>
        <div>
          <p className="text-xs text-slate-500 font-mono uppercase tracking-tighter">
            Authenticated Session
          </p>
          <p className="text-sm font-semibold text-white">
            {user?.email ?? "Unknown"}
          </p>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-2 px-2 py-1 bg-white/5 rounded-md border border-white/5">
        <ShieldCheck size={14} className="text-emerald-400" />
        <span className="text-[10px] font-bold text-slate-300 uppercase">
          {user?.role?.name}
        </span>
      </div>

      {/* Handles for connecting to other nodes */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-2 h-2 bg-indigo-500 border-none"
      />
    </div>
  );
}
