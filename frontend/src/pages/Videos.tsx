import { useEffect, useState } from "react";
import axios from "axios";
import VideoComponent from "../components/VideoComponent.tsx";

interface ApiResponse {
  videos: string[];
}

function Videos() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_URL}/videos`,
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
      <>
        <p>Something went wrong.</p>
        <p>{error}</p>
      </>
    );
  }
  if (!data) return <p>Loading...</p>;

  return (
    <>
      <div className="d-flex flex-column align-items-center">
        {data.videos.map((item) => (
          <VideoComponent videoID={item} key={item} />
        ))}
      </div>
    </>
  );
}

export default Videos;
