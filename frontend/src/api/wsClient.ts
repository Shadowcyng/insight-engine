// src/api/wsClient.ts
import { addLog } from "@/store/logStore";
import { atom } from "nanostores";
import { $nodes } from "@/store/canvasStore";

export const $socket = atom<WebSocket | null>(null);

export function connectLogs() {
  const socket = new WebSocket("ws://localhost/api/v1/ws/logs");

  socket.onopen = () => {
    addLog("Stream Connected", "success");
    $socket.set(socket);
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // Minor comment: Route 'log' types to the LogNode store
    if (
      data.type === "log" ||
      data.type === "info" ||
      data.type === "success"
    ) {
      addLog(data.message, data.type);
    }

    // Minor comment: Route 'query_result' to the specific Node on the canvas
    if (data.type === "query_result") {
      const currentNodes = $nodes.get();
      const updatedNodes = currentNodes.map((node) => {
        // We match by upload_id or node data (assuming 1:1 for now)
        if (node.data.upload_id === data.upload_id) {
          return {
            ...node,
            data: { ...node.data, answer: data.answer, loading: false },
          };
        }
        return node;
      });
      $nodes.set(updatedNodes);
    }
    if (data.type === "summary_ready") {
      const nodes = $nodes.get();
      const updatedNodes = nodes.map((node) => {
        // Minor comment: Only update the node that matches this specific upload
        if (
          node.type === "fileNode" &&
          node.data.upload_id === data.upload_id
        ) {
          return {
            ...node,
            data: { ...node.data, ai_summary: data.summary, status: "ready" },
          };
        }
        return node;
      });
      $nodes.set(updatedNodes);
    }

    if (data.type === "summary_ready") {
      // Minor comment: Find the specific file node and inject the summary
      const currentNodes = $nodes.get();
      $nodes.set(
        currentNodes.map((node) => {
          if (node.data.upload_id === data.upload_id) {
            return {
              ...node,
              data: { ...node.data, ai_summary: data.summary },
            };
          }
          return node;
        }),
      );
      addLog(`AI Summary generated for ${data.filename}`, "success");
    }
  };

  socket.onclose = () => {
    addLog("Stream Disconnected. Retrying...", "error");
    $socket.set(null);
    setTimeout(connectLogs, 5000);
  };

  return socket;
}
