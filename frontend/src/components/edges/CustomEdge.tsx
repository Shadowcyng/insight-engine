// src/components/dashboard/edges/ButtonEdge.tsx
import {
  BaseEdge,
  EdgeLabelRenderer,
  type EdgeProps,
  getBezierPath,
} from "@xyflow/react";

export default function ButtonEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  ...props
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  return (
    <>
      <BaseEdge path={edgePath} {...props} />
      <EdgeLabelRenderer>
        <button
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: "all",
          }}
          className="bg-red-500 text-white rounded-full w-4 h-4 text-[10px] flex items-center justify-center hover:bg-red-600 shadow-lg"
          onClick={() => {
            // Trigger your edge deletion logic here
          }}
        >
          ×
        </button>
      </EdgeLabelRenderer>
    </>
  );
}
