import { Link } from "react-router-dom";
import Line from "./Line";
import {
  CircleUserRound,
  Wrench,
  HardDriveDownload,
  LayoutDashboard,
  House,
  LogOut,
  Film,
  Info,
} from "lucide-react";
import { useSearchParams } from "react-router-dom";

function SideBar() {
  const [searchParams] = useSearchParams();

  let adminTab = (
    <>
      <Line />
      <Link
        to={`dashboard?${searchParams.toString()}`}
        className="btn btn-darker px-1 ps-2 ms-2"
      >
        <div className="d-flex justify-content-center align-items-center">
          <LayoutDashboard size={18} color={"Grey"} className="me-2" />
          <div className="text-white-50">Admin Dashboard</div>
          <div className="me-auto"></div>
        </div>
      </Link>
    </>
  );

  if (searchParams.get("admin") !== "true") {
    adminTab = <></>;
  }

  return (
    <>
      <nav className="navbar navbar-dark bg-darker px-2 min-vh-100 d-flex flex-column justify-content-start flex-shrink-0">
        <div className="overflow-auto px-1 pb-3 pt-1 d-flex flex-column flex-grow-1 justify-content-start align-items-stretch">
          <div className="p-2 logo">
            <div className="d-flex justify-content-center align-items-center">
              <HardDriveDownload size={22} className="me-3" />
              <b className="text-white">App-Name</b>
              <div className="me-5"></div>
              <div className="me-3"></div>
            </div>
          </div>
          <Line />

          <Link
            to={`/?${searchParams.toString()}`}
            className="btn btn-darker px-1 ps-2 ms-2"
          >
            <div className="d-flex justify-content-center align-items-center">
              <House size={18} color={"Grey"} className="me-2" />
              <div className="text-white-50">Home</div>
              <div className="me-auto"></div>
            </div>
          </Link>

          <Link
            to={`tasks?${searchParams.toString()}`}
            className="btn btn-darker px-1 ps-2 ms-2"
          >
            <div className="d-flex justify-content-center align-items-center">
              <Wrench size={18} color={"Grey"} className="me-2" />
              <div className="text-white-50">Tasks</div>
              <div className="me-auto"></div>
            </div>
          </Link>

          <Link
            to={`videos?${searchParams.toString()}`}
            className="btn btn-darker px-1 ps-2 ms-2"
          >
            <div className="d-flex justify-content-center align-items-center">
              <Film size={18} color={"Grey"} className="me-2" />
              <div className="text-white-50">Videos</div>
              <div className="me-auto"></div>
            </div>
          </Link>

          <Link
            to={`/help?${searchParams.toString()}`}
            className="btn btn-darker px-1 ps-2 ms-2"
          >
            <div className="d-flex justify-content-center align-items-center">
              <Info size={18} color={"Grey"} className="me-2" />
              <div className="text-white-50">Help</div>
              <div className="me-auto"></div>
            </div>
          </Link>

          {adminTab}

          <div className="mt-auto spacer"></div>
          <Line />
          <Link
            to={`login?${searchParams.toString()}`}
            className="btn btn-darker px-1 ps-2"
          >
            <div className="d-flex justify-content-center align-items-center">
              <CircleUserRound size={18} color={"Grey"} className="me-2" />
              <div className="text-white">Account</div>
              <div className="me-auto"></div>
            </div>
          </Link>

          <Link
            to={`logout?${searchParams.toString()}`}
            className="btn btn-darker px-1 ps-2"
          >
            <div className="d-flex justify-content-center align-items-center">
              <LogOut size={18} color={"rgb(220, 53, 69)"} className="me-2" />
              <div className="text-danger">Logout</div>
              <div className="me-auto"></div>
            </div>
          </Link>
        </div>
      </nav>
    </>
  );
}

export default SideBar;
