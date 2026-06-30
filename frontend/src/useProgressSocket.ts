// hooks/useProgressSocket.ts
import { useEffect, useRef, useState, useCallback } from "react";

export type ProgressMessage = {
  current_process: string;
  current_video_progress: number;
  current_process_progress: number;
  current_process_video_count: string;
  process_eta: number;
  current_video_id: string;
};

export function useProgressSocket(url: string) {
  const ws = useRef<WebSocket | null>(null);
  const [progress, setProgress] = useState<ProgressMessage | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      setConnected(true);
      console.log("WS connected");
    };

    ws.current.onmessage = (event) => {
      const msg: ProgressMessage = JSON.parse(event.data);
      setProgress(msg);
    };

    ws.current.onclose = () => setConnected(false);
    ws.current.onerror = (e) => console.error("WS error", e);

    return () => ws.current?.close(); // cleanup on unmount
  }, [url]);

  // Send a command to the server
  const send = useCallback((msg: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(msg);
    }
  }, []);

  return { progress, connected, send };
}
