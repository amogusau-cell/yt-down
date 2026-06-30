import { Button, Form } from "react-bootstrap";

import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ChevronLeft } from "lucide-react";
import CreateComponent from "../components/CreateComponent.tsx";
import axios from "axios";

function SelectedTask() {
  const [searchParams] = useSearchParams();
  const [link, setLink] = useState("");
  const [type, setType] = useState("");
  const [placeholder, setPlaceholder] = useState("");
  const [text, setText] = useState("Url: ");
  const [btnText, setBtnText] = useState("Select type");
  const [btnActive, setBtnActive] = useState(false);
  const [items, setItems] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [checked, setChecked] = useState(false);

  const navigate = useNavigate();

  const [title, setTitle] = useState("");

  const [playlisError, setPlaylistError] = useState<string>();

  const addItem = (value: string) => {
    setItems((prev) => [...prev, value]);
  };
  const removeItem = (value: string) => {
    setItems((prev) => prev.filter((item) => item !== value));
  };
  const clearItems = () => setItems([]);

  const [id, setId] = useState("");

  const bottom_content = <></>;

  const getPlaylistVideos = async (id: string) => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/playlist/${id}/detail`,
        {
          headers: {
            token: localStorage.getItem("token"),
          },
        },
      );
      setItems(response.data);
      setLoading(false);
    } catch (err) {
      setPlaylistError(JSON.stringify(err));
      console.log(err);
    }
  };

  const createTask = async () => {
    try {
      const formData = new FormData();
      formData.append("type", type);
      formData.append("playlist", id);
      formData.append("title", title);
      formData.append("process", JSON.stringify(items));
      formData.append("private", checked ? "true" : "false");

      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/process`,
        formData,
        {
          headers: {
            token: localStorage.getItem("token"),
          },
        },
      );
      setItems(response.data);
      setLoading(false);
    } catch (err) {
      setPlaylistError(JSON.stringify(err));
      console.log(err);
    }
  };

  return (
    <>
      <div className="bg-darker rounded text-light w-100 min-h-100 d-flex overflow-hidden p-4">
        <div className="d-flex flex-column overflow-hidden">
          <div>
            <Link
              to={`/tasks?${searchParams.toString()}`}
              className="btn btn-darker mb-1"
            >
              <ChevronLeft size={22} color={"Grey"} className="m-0 p-0" />
            </Link>
          </div>
          <h1 className="pb-2">Create Task</h1>
          <Form.Group className="my-3 text-light">
            <Form.Label className="text-light">Title:</Form.Label>
            <Form.Control
              className="w-100 btn btn-dark align-items-start text-start"
              type="text"
              placeholder={"Title"}
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
              }}
            />
          </Form.Group>
          <Form.Group>
            <Form.Label>Task type</Form.Label>
            <Form.Select
              className="w-100 btn btn-dark align-items-start text-start"
              style={{ marginRight: "10rem" }}
              value={type}
              onChange={(e) => {
                setType(e.target.value);
                if (e.target.value == "video") {
                  setPlaceholder("https://www.youtube.com/watch?v=...");
                  setText("Video Url:");
                  setLink("");
                  setBtnText("Add video");
                  setId("");
                } else if (e.target.value == "playlist") {
                  setPlaceholder("https://www.youtube.com/playlist?list=...");
                  setText("Playlist Url:");
                  setLink("");
                  setBtnText("Check playlist");
                  setId("");
                  clearItems();
                } else {
                  setPlaceholder("");
                  setText("Select type");
                  setBtnActive(false);
                  setLink("");
                  clearItems();
                }
              }}
            >
              <option value="">-- Select type --</option>
              <option value="video">Video</option>
              <option value="playlist">Playlist</option>
            </Form.Select>
          </Form.Group>

          <Form.Group className="mt-3 text-light">
            <Form.Label className="text-light">{text}</Form.Label>
            <Form.Control
              className="w-100 btn btn-dark align-items-start text-start"
              type="text"
              placeholder={placeholder}
              value={link}
              onChange={(e) => {
                setLink(e.target.value);
                if (type == "video") {
                  if (
                    e.target.value.startsWith(
                      "https://www.youtube.com/watch?v=",
                    )
                  ) {
                    const videoId = e.target.value
                      .slice("https://www.youtube.com/watch?v=".length)
                      .split("&")[0];

                    setId(videoId);
                    setBtnActive(true);
                  } else {
                    setId("");
                    setBtnActive(false);
                    clearItems();
                  }
                } else if (type == "playlist") {
                  if (
                    e.target.value.startsWith(
                      "https://www.youtube.com/playlist?list=",
                    )
                  ) {
                    const videoId = e.target.value
                      .slice("https://www.youtube.com/playlist?list=".length)
                      .split("&")[0];
                    setId(videoId);
                    clearItems();
                    setBtnActive(true);
                  } else {
                    clearItems();
                    setId("");
                    setBtnActive(false);
                  }
                }
              }}
            />
            {bottom_content}
            <Form.Label className="text-secondary">{id}</Form.Label>
          </Form.Group>

          <Button
            variant="primary"
            className={btnActive ? "mt-2" : "disabled mt-2"}
            onClick={() => {
              if (type == "video") {
                addItem(id);
              } else if (type == "playlist") {
                clearItems();
                getPlaylistVideos(id);
                setLoading(true);
              }
            }}
          >
            {btnText}
          </Button>

          <Form.Check
            id="my-switch"
            className="form-switch d-flex align-items-center gap-2 mt-2" // ← form-switch here
          >
            <Form.Check.Input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
              style={{ width: "3rem", height: "1.5rem", cursor: "pointer" }}
            />
            <Form.Check.Label>
              {checked ? "Hidden" : "Not hidden"}
            </Form.Check.Label>
          </Form.Check>

          <Button
            variant="success"
            className={items.length != 0 ? "mt-4" : "disabled mt-4"}
            onClick={() => {
              createTask();
              navigate("/tasks");
            }}
          >
            Create Task
          </Button>
        </div>
        <div className="d-flex flex-column overflow-hidden ms-4 mt-3">
          {playlisError ? "Something went wrong" : ""}
          {loading ? "Loading playlist..." : ""}
          <ul className="list-group gap-1 py-1">
            {items.map((item: string) => (
              <div key={item}>
                {item == "" ? (
                  <></>
                ) : (
                  <CreateComponent
                    videoID={item}
                    removeItem={removeItem}
                    playlist={type == "video"}
                  />
                )}
              </div>
            ))}
          </ul>
        </div>
      </div>
    </>
  );
}

export default SelectedTask;
