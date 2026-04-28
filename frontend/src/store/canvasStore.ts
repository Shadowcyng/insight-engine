import { atom, onSet } from "nanostores";
import { type Node, type Edge } from "@xyflow/react";

// Minor comment: This allows us to update nodes from anywhere in the app
export const $nodes = atom<Node[]>([]);
export const $edges = atom<Edge[]>([]);

onSet($nodes, ({ newValue }) => {
  localStorage.setItem("insight_engine_nodes", JSON.stringify(newValue));
});

export const addNode = (node: Node) => $nodes.set([...$nodes.get(), node]);

export function hydrateCanvas() {
  const saved = localStorage.getItem("insight_engine_nodes");
  if (saved) {
    $nodes.set(JSON.parse(saved));
  }
}
