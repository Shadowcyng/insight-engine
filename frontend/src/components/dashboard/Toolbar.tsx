// src/components/dashboard/Toolbar.tsx
import { FilePlus, MessageSquare, Activity } from "lucide-react";
import { addNode } from "@/store/canvasStore";

export function Toolbar() {
  const createNode = (type: "fileNode" | "queryNode" | "logNode") => {
    // Minor comment: Offset position slightly so nodes don't stack perfectly
    const position = {
      x: 100 + Math.random() * 200,
      y: 100 + Math.random() * 200,
    };

    addNode({
      id: `${type}-${Date.now()}`,
      type,
      position,
      data: { status: "idle", answer: "" },
    });
  };

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 flex items-center gap-1 p-1.5 bg-slate-900/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl ">
      <ToolbarButton
        icon={<FilePlus size={18} />}
        label="Data Source"
        onClick={() => createNode("fileNode")}
        color="text-indigo-400"
      />
      <div className="w-px h-4 bg-white/10 mx-1" />
      <ToolbarButton
        icon={<MessageSquare size={18} />}
        label="Query Engine"
        onClick={() => createNode("queryNode")}
        color="text-blue-400"
      />
      <div className="w-px h-4 bg-white/10 mx-1" />
      <ToolbarButton
        icon={<Activity size={18} />}
        label="Execution Log"
        onClick={() => createNode("logNode")}
        color="text-emerald-400"
      />
    </div>
  );
}

function ToolbarButton({ icon, label, onClick, color }: any) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 hover:bg-white/5 rounded-xl transition-all group"
    >
      <span className={`${color} group-hover:scale-110 transition-transform`}>
        {icon}
      </span>
      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
        {label}
      </span>
    </button>
  );
}
