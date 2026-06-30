import { useEffect, useState } from "react";
import axios from "axios";
import { Trash2Icon } from "lucide-react";
import { Button } from "react-bootstrap";

interface ApiResponse {
  id: string;
  title: string;
  thumbnail: string;
  channel: string;
}

function CreateComponent({
  videoID,
  removeItem,
  playlist,
}: {
  videoID: string;
  removeItem: (id: string) => void;
  playlist: boolean;
}) {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_URL}/videos/${videoID}/detail`,
          {
            headers: {
              token: localStorage.getItem("token"),
            },
          },
        );

        setData(response.data); // axios unwraps .data automatically
      } catch (err) {
        setError(JSON.stringify(err));
        console.log(err);
      }
    };

    fetchData();
  }, []);

  if (error) {
    return (
      <div
        className="bg-dark rounded text-light w-100 d-flex overflow-hidden my-2 p-3 align-items-start"
        style={{ minHeight: "135px", minWidth: "400px" }}
      >
        <p>{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div
        className="bg-dark rounded text-light w-100 d-flex overflow-hidden my-2 p-3 align-items-start"
        style={{ minHeight: "135px", minWidth: "400px" }}
      >
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div
      className="bg-dark rounded text-light w-100 d-flex overflow-hidden my-2 p-3 align-items-start"
      style={{ minHeight: "135px", minWidth: "400px" }}
    >
      <img
        src={`${import.meta.env.VITE_API_URL}/${localStorage.getItem("token")}/videos/${videoID}/thumbnail`}
        alt="Video Thumbnail"
        className="rounded img-fluid"
        style={{ width: "30%", height: "auto", minWidth: "240px" }}
      />
      <div className="ms-3 d-flex align-items-start justify-content-start flex-grow-1">
        <div className="d-flex align-items-start flex-column flex-grow-1">
          <h6>{data.title}</h6>
          <p>{data.channel}</p>
          <p className="mb-0">Id: {data.id}</p>
        </div>
      </div>
      <div className="ms-3 d-flex align-items-start justify-content-end flex-grow-1">
        <Button
          variant="dark"
          className={playlist ? "" : "disabled"}
          onClick={() => {
            removeItem(videoID);
          }}
        >
          <Trash2Icon color={"rgb(220, 53, 69)"} />
        </Button>
      </div>
    </div>
  );
}

export default CreateComponent;
