import { useEffect, useState } from "react";
import axios from "axios";

interface ApiResponse {
  id: string;
  title: string;
  thumbnail: string;
  channel: string;
}

function TaskComponentSelected({ videoID }: { videoID: string }) {
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
          <p>Id: {data.id}</p>
        </div>
      </div>
    </div>
  );
}

export default TaskComponentSelected;
