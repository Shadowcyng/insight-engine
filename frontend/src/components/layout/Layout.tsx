import React from "react";
import { useStore } from "@nanostores/react";
import { $ui, toggleSidebar } from "@/store/uiStore";

const Layout = () => {
  // Minor comment: This component automatically re-renders ONLY when $ui changes
  const uiState = useStore($ui);

  return;
  <aside className={`sidebar ${uiState.isSidebarOpen ? "open" : "closed"}`}>
    <nav>{/* Navigation links go here */}</nav>

    <button onClick={toggleSidebar}>
      {uiState.isSidebarOpen ? "Close Menu" : "Open Menu"}
    </button>
  </aside>;
};

export default Layout;
