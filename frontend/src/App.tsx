import { BrowserRouter, Route, Routes } from "react-router-dom";
import SideBar from "./components/SideBar";
import Test from "./components/Test";
import TasksPage from "./pages/TasksPage";
import SelectedTask from "./pages/SelectedTaskPage";
import CreateTask from "./pages/CreateTask.tsx";
import Videos from "./pages/Videos.tsx";
import Logout from "./pages/Logout.tsx";
import Login from "./pages/Login.tsx";
import Register from "./pages/Register.tsx";
import AdminRegister1 from "./pages/AdminRegister1.tsx";
import AdminRegister2 from "./pages/AdminRegister2.tsx";
import LoginToken from "./pages/LoginToken.tsx";
import Help from "./components/Help.tsx";

function App() {
  if (localStorage.getItem("token") === null) {
    return (
      <BrowserRouter>
        <div className="bg-black border-danger text-light vh-100 vw-100 d-flex overflow-hidden">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/admin" element={<AdminRegister1 />} />
            <Route path="/admin/2" element={<AdminRegister2 />} />
            <Route path="/token" element={<LoginToken />} />
            <Route path="/help/*" element={<Help />} />
          </Routes>
        </div>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <div className="bg-black border-danger text-light vh-100 vw-100 d-flex overflow-hidden">
        <SideBar />
        <main className="p-3 flex-grow-1 overflow-auto">
          <Routes>
            <Route path="/" element={<div />} />
            <Route path="/test" element={<Test />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/tasks/create" element={<CreateTask />} />
            <Route path="/tasks/:id" element={<SelectedTask />} />
            <Route path="/videos" element={<Videos />} />
            <Route path="/logout" element={<Logout />} />
            <Route path="/login" element={<Login />} />
            <Route path="/help/*" element={<Help />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
