import HelpSideBar from "./HelpSideBar.tsx";
import { Route, Routes } from "react-router-dom";

import indexMd from "../Help/index.md?raw";
import taskMd from "../Help/task.md?raw";
import MD from "../pages/MD.tsx";

function Help() {
  return (
    <div className="d-flex flex-row w-100 h-100">
      <HelpSideBar />
      <main className="p-3 flex-grow-1 overflow-auto">
        <Routes>
          <Route path="/" element={<MD content={indexMd} />} />
          <Route path="/task" element={<MD content={taskMd} />} />
        </Routes>
      </main>
    </div>
  );
}

export default Help;
