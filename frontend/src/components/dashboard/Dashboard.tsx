import { Canvas } from "./Canvas";
import { Toolbar } from "./Toolbar";

export function Dashboard() {
  return (
    <div className="relative w-full h-screen bg-slate-950">
      {/* The Canvas */}
      <div className="absolute inset-0">
        <Canvas />
      </div>

      {/* The Toolbar - Positioned on top */}
      <Toolbar />
    </div>
  );
}
