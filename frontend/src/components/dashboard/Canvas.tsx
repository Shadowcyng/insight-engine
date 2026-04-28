// src/components/dashboard/Canvas.tsx
import { useCallback, useEffect } from "react";
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type Connection,
  type Edge,
  addEdge,
} from "@xyflow/react";
import { useStore } from "@nanostores/react";
import { $nodes, $edges, hydrateCanvas } from "@/store/canvasStore";
import { UserNode } from "./nodes/UserNode";
import { LogNode } from "./nodes/LogNode";
import { addLog } from "@/store/logStore";
import { connectLogs } from "@/api/wsClient";
import { QueryNode } from "./nodes/QueryNode";
import { FileNode } from "./nodes/FileNode";
import { Toolbar } from "./Toolbar";

// Minor comment: Register your custom node types
const nodeTypes = {
  userNode: UserNode,
  logNode: LogNode,
  queryNode: QueryNode,
  fileNode: FileNode,
};

setTimeout(() => addLog("Initializing Insight Engine...", "info"), 1000);
setTimeout(() => addLog("Connected to PostgreSQL", "success"), 2500);

export function Canvas() {
  const storeNodes = useStore($nodes);
  const storeEdges = useStore($edges);
  const [nodes, setNodes, onNodesChange] = useNodesState(storeNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(storeEdges);

  // Sync store nodes when local nodes change
  useEffect(() => {
    $nodes.set(nodes);
  }, [nodes]);

  // Sync store edges when local edges change
  useEffect(() => {
    $edges.set(edges);
  }, [edges]);

  const onConnect = useCallback(
    (params: Connection) => {
      // Minor comment: Create a beautiful animated edge
      const { source, target } = params;
      // Minor comment: Find the source node to get the upload_id
      const sourceNode = nodes.find((n) => n.id === source);
      const targetNode = nodes.find((n) => n.id === target);
      console.log("sourceNode?.data.status", sourceNode?.data.status);
      if (sourceNode?.data.status === "ready") {
        // Proceed with handshake...
        if (
          sourceNode &&
          sourceNode.type === "fileNode" &&
          targetNode?.type === "queryNode"
        ) {
          const uploadId = sourceNode.data.upload_id;

          // Minor comment: Inject the upload_id into the QueryNode's data
          const updatedNodes = nodes.map((node) => {
            if (node.id === target) {
              return { ...node, data: { ...node.data, upload_id: uploadId } };
            }
            return node;
          });
          setNodes(updatedNodes);
        }
        const newEdge: Edge = {
          ...params,
          id: `e-${source}-${target}`,
          animated: true,
          style: { stroke: "#6366f1", strokeWidth: 2 },
        };
        setEdges(addEdge(newEdge, edges));
      }
    },
    [nodes, edges, setNodes, setEdges],
  );

  const onEdgesDelete = useCallback(
    (deletedEdges: Edge[]) => {
      const updatedNodes = nodes.map((node) => {
        // If this node was the target of a deleted edge, clear its data
        const wasTarget = deletedEdges.some((edge) => edge.target === node.id);
        if (wasTarget && node.type === "queryNode") {
          return {
            ...node,
            data: { ...node.data, upload_id: null, answer: "" },
          };
        }
        return node;
      });
      setNodes(updatedNodes);
    },
    [nodes],
  );

  // Hydrate canvas from localStorage and initialize nodes
  useEffect(() => {
    const saved = localStorage.getItem("insight_engine_nodes");
    if (saved) {
      try {
        hydrateCanvas();
      } catch (error) {
        console.error("Failed to parse saved nodes", error);
      }
    }

    // Initialize with default nodes if no saved data
    setNodes([
      {
        id: "session-1",
        type: "userNode",
        position: { x: 50, y: 250 },
        data: {},
        draggable: true,
      },
      {
        id: "file-1",
        type: "fileNode",
        position: { x: 400, y: 250 },
        data: { status: "idle", upload_id: null },
        draggable: true,
      },
      {
        id: "query-1",
        type: "queryNode",
        position: { x: 800, y: 250 },
        data: { upload_id: null, answer: "" },
        draggable: true,
      },
      {
        id: "logs-1",
        type: "logNode",
        position: { x: 400, y: 500 },
        data: {},
        draggable: true,
      },
    ]);
  }, [setNodes]);

  // Initialize websocket connection for logs
  useEffect(() => {
    const ws = connectLogs();
    return () => ws.close();
  }, []);

  return (
    <div className="h-screen w-full bg-slate-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onConnect={onConnect}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onEdgesDelete={onEdgesDelete}
        // draggable
        fitView
        colorMode="dark"
      >
        <Background color="#1e293b" variant={BackgroundVariant.Dots} gap={20} />
        {/* <Toolbar /> */}
      </ReactFlow>
    </div>
  );
}
