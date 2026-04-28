// src/store/logStore.ts
import { atom } from "nanostores";

export interface LogEntry {
  id: string;
  message: string;
  type: "info" | "error" | "success";
  timestamp: string;
}

// Minor comment: Holds the last 50 logs to prevent memory bloat
export const $agentLogs = atom<LogEntry[]>([]);

export function addLog(message: string, type: LogEntry["type"] = "info") {
  const newLog = {
    id: Math.random().toString(36),
    message,
    type,
    timestamp: new Date().toLocaleTimeString(),
  };
  $agentLogs.set([...$agentLogs.get().slice(-49), newLog]);
}
