import { Button, Form } from "react-bootstrap";
import { useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [loading, setLoading] = useState("");

  const [same, setSame] = useState("Password is empty");

  const [canSubmit, setCanSubmit] = useState(false);

  const register = async () => {
    try {
      const formData = new FormData();
      formData.append("username", username);
      formData.append("password", password);

      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/register`,
        formData,
      );
      setMessage(response.data);
      setLoading("");
    } catch (err) {
      setError(JSON.stringify(err));
      console.log(err);
      setLoading("");
    }
  };

  return (
    <>
      <div className="d-flex flex-column align-items-center justify-content-center w-100">
        <h3>Register</h3>
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
              if (e.target.value == "") {
                setSame("Password is empty");
                setCanSubmit(false);
                return;
              } else {
                setSame("");
                setCanSubmit(true);
              }
              if (e.target.value != password2) {
                setSame("Password does not match");
                setCanSubmit(false);
              } else {
                setSame("");
                setCanSubmit(true);
              }
            }}
          />
        </Form.Group>
        <Form.Group className="mt-1 text-light w-25 mx-5">
          <Form.Control
            className="w-100 btn btn-dark align-items-start text-start"
            type="password"
            placeholder="Retype password"
            value={password2}
            onChange={(e) => {
              setPassword2(e.target.value);
              if (password != e.target.value) {
                setSame("Password does not match");
                setCanSubmit(false);
              } else {
                setSame("");
                setCanSubmit(true);
              }
            }}
          />

          <Form.Label className="text-danger">{same}</Form.Label>
        </Form.Group>

        <Button
          variant="primary"
          className={canSubmit ? "w-25 mt-4" : "disabled w-25 mt-4"}
          onClick={() => {
            setLoading("Loading...");
            register().then(() => {
              if (error) {
                console.log("error:", error);
              }
            });
          }}
        >
          Register
        </Button>
        <p>{loading}</p>
        {error && (
          <p>
            User already exists. If you suspect this is an error more info is at
            console.
          </p>
        )}
        {message == "User created successfully" ? (
          <div className="d-flex gap-2 alert alert-success" role="alert">
            <p className="mb-0">User created successfully</p>
            <Link to="/">Go to login page</Link>
          </div>
        ) : (
          <Link className="text-secondary" to="/">
            Back
          </Link>
        )}
      </div>
    </>
  );
}

export default Register;
