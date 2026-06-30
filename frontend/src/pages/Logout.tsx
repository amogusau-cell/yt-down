import { useNavigate } from "react-router-dom";
import { useEffect } from "react";

function Logout() {
  const navigate = useNavigate();

  localStorage.removeItem("token");

  useEffect(() => {
    navigate("/");
  }, []);

  return (
    <>
      <p>Logging out...</p>
    </>
  );
}

export default Logout;
