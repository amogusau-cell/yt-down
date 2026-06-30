import { Button, Form } from "react-bootstrap";
import { useState } from "react";
import { Link } from "react-router-dom";

function LoginToken() {
  const [token, setToken] = useState("");
  return (
    <>
      <div className="d-flex flex-column align-items-center justify-content-center w-100">
        <h3>Login with token</h3>
        <p className="mb-0 mt-3">Token</p>
        <Form.Group className="mt-1 text-light mx-5" style={{ width: "95%" }}>
          <Form.Control
            className="w-100 btn btn-dark align-items-start text-start"
            type="token"
            placeholder="Token"
            value={token}
            onChange={(e) => {
              setToken(e.target.value);
            }}
          />

          <Form.Label className="text-secondary"></Form.Label>
        </Form.Group>

        <Button
          variant="primary"
          className="w-25 mt-4"
          onClick={() => {
            localStorage.setItem("token", token);
            window.location.href = "/";
          }}
        >
          Login
        </Button>

        <p className="text-secondary mt-4">
          Note that token will not be checked.
        </p>

        <div className="d-flex gap-2">
          <Link to="/" className="text-secondary">
            Back
          </Link>
          <Link to="/help/token-login" className="text-secondary">
            Help
          </Link>
        </div>
      </div>
    </>
  );
}

export default LoginToken;
