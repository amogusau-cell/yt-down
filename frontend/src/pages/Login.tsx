import { Button, Form } from "react-bootstrap";
import { useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const [loading, setLoading] = useState("");

  const login = async () => {
    try {
      const formData = new FormData();
      formData.append("username", username);
      formData.append("password", password);

      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/login`,
        formData,
      );
      setLoading("");
      localStorage.setItem("token", response.data);
      window.location.href = "/";
    } catch (err) {
      setError(JSON.stringify(err));
      console.log(err);
      setLoading("");
    }
  };

  return (
    <>
      <div className="d-flex flex-column align-items-center justify-content-center w-100">
        <h3>Login</h3>
        <p className="mb-0 mt-3">Username</p>
        <Form.Group className="mt-1 text-light w-25 mx-5">
          <Form.Control
            className="w-100 btn btn-dark align-items-start text-start"
            type="text"
            placeholder={"Username"}
            value={username}
            onChange={(e) => {
              setUsername(e.target.value);
            }}
          />
          <Form.Label className="text-secondary"></Form.Label>
        </Form.Group>

        <p className="mb-0 mt-3">Password</p>
        <Form.Group className="mt-1 text-light w-25 mx-5">
          <Form.Control
            className="w-100 btn btn-dark align-items-start text-start"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
            }}
          />

          <Form.Label className="text-secondary"></Form.Label>
        </Form.Group>

        <Button
          variant="primary"
          className="w-25 mt-4"
          onClick={() => {
            setLoading("Loading...");
            login().then(() => {
              if (error) {
                console.log("error:", error);
              }
            });
          }}
        >
          Login
        </Button>
        <p>{loading}</p>
        {error && (
          <p>
            Username or password incorrect. If you suspect this is an error more
            info is at console.
          </p>
        )}
        <div className="d-flex flex-row gap-2">
          <Link to="/register" className="text-secondary">
            Register
          </Link>
          <p className="text-secondary">{" - "}</p>
          <Link to="/admin" className="text-secondary">
            Admin Register
          </Link>
          <p className="text-secondary">{" - "}</p>
          <Link to="/token" className="text-secondary">
            Login With Token
          </Link>
          <p className="text-secondary">{" - "}</p>
          <Link to="/help" className="text-secondary">
            Help
          </Link>
        </div>
      </div>
    </>
  );
}

export default Login;
