import { Link } from "react-router-dom";
import Line from "./Line";
import { Info } from "lucide-react";

function SideBar() {
  return (
    <>
      <nav className="navbar navbar-dark bg-darker px-2 h-100 d-flex flex-column justify-content-start flex-shrink-0">
        <div className="overflow-auto px-1 pb-3 pt-1 d-flex flex-column flex-grow-1 justify-content-start align-items-stretch">
          <div className="p-2 logo">
            <div className="d-flex justify-content-start align-items-center">
              <Info size={22} className="me-3" />
              <b className="text-white">Help</b>
              <div className="me-5"></div>
              <div className="me-3"></div>
            </div>
          </div>
          <Line />

          <Link to={`/help`} className="btn btn-darker px-1 ps-2 ms-2">
            <div className="d-flex justify-content-center align-items-center">
              <div className="text-white-50">How to use</div>
              <div className="me-auto"></div>
            </div>
          </Link>

          <Link to={`/help/task`} className="btn btn-darker px-1 ps-2 ms-2">
            <div className="d-flex justify-content-center align-items-center">
              <div className="text-white-50">Tasks</div>
              <div className="me-auto"></div>
            </div>
          </Link>
        </div>
      </nav>
    </>
  );
}

export default SideBar;
