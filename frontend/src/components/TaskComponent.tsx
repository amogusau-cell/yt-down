import { Link, useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import { useProgressSocket } from "../useProgressSocket.ts";

interface ApiResponse {
  videos: string;
  id: string;
  title: string;
  playlist: string;
  private: boolean;
  finished: boolean;
  owner: string;
  type: string;
  can_see: boolean;
}

interface StatusMessage {
  current_process: string;
  current_video_progress: number;
  current_process_progress: number;
  current_process_video_count: string;
  process_eta: number;
  current_video_id: string;
}

function TaskComponent({
  id,
  set,
}: {
  id: string;
  set: React.Dispatch<React.SetStateAction<boolean | null>>;
}) {
  const [searchParams] = useSearchParams();
  const [data, setData] = useState<ApiResponse | null>(null);
  const [statusData, statusSetData] = useState<StatusMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { progress, connected, send } = useProgressSocket(
    `${import.meta.env.VITE_WS_URL}/ws/progress`,
  );

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_URL}/process/${id}`,
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

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statusResponse = await axios.get(
          `${import.meta.env.VITE_API_URL}/status`,
          {
            headers: {
              token: localStorage.getItem("token"),
            },
          },
        );

        statusSetData(statusResponse.data[0]); // axios unwraps .data automatically
      } catch (err) {
        setError(JSON.stringify(err));
        console.log(err);
      }
    };

    fetchData();
  }, []);

  if (error) {
    return (
      <div className="btn btn-dark text-light w-100 d-flex overflow-hidden my-2 p-3 align-items-center">
        <img
          src={`/src/assets/hidden.png`}
          alt="Task icon"
          className="rounded img-fluid"
          style={{ width: "240px", height: "auto" }}
        />
        <div className="ms-3 d-flex flex-column align-items-start flex-grow-1">
          <p>Error: {error}</p>
        </div>
      </div>
    );
  }

  if (!data)
    return (
      <div className="btn btn-dark text-light w-100 d-flex overflow-hidden my-2 p-3 align-items-center">
        <img
          src={`/src/assets/hidden.png`}
          alt="Task icon"
          className="rounded img-fluid"
          style={{ width: "240px", height: "auto" }}
        />
        <div className="ms-3 d-flex flex-column align-items-start flex-grow-1">
          <p>Loading...</p>
        </div>
      </div>
    );

  if (data.finished) {
    return <></>;
  } else {
    set(true);
  }

  let progress_bar = <></>;
  if (statusData?.current_process == id) {
    send("start");

    const processProgress = progress?.current_process_progress ?? 0;
    const videoProgress = progress?.current_video_progress ?? 0;
    const videoCount = progress?.current_process_video_count
      ? Number(progress.current_process_video_count)
      : 0;

    const percent =
      videoCount > 0
        ? processProgress + videoProgress / videoCount
        : processProgress;

    progress_bar = (
      <>
        <div className="w-100">
          {connected ? (
            <p className="text-success mb-1 mt-2 text-start">Connected</p>
          ) : (
            <p className="text-danger mb-1 mt-2 text-start">Disconnected</p>
          )}
          <div
            className="progress rounded-pill"
            style={{ height: "1.25rem", width: "100%" }}
          >
            <div
              className="progress-bar bg-success rounded-pill"
              role="progressbar"
              style={{ width: `${percent}%` }}
              aria-valuenow={videoProgress}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              {percent.toFixed(1)}%
            </div>
          </div>
        </div>
      </>
    );
  }

  let content;
  if (data.type == "video") {
    content = (
      <>
        <p className="mb-0 my-1">Type: Video</p>
        <p className="mb-0 my-1">Videos: {JSON.parse(data.videos).length}</p>
      </>
    );
  } else {
    content = (
      <>
        <p className="mb-0 my-1">Type: Playlist</p>
        <p className="mb-0 my-1">Playlist: {data.playlist}</p>
      </>
    );
  }

  if (!data.can_see) {
    return (
      <div className="btn btn-dark disabled text-light w-100 d-flex overflow-hidden my-2 p-3 align-items-center">
        <img
          src={`/src/assets/hidden.png`}
          alt="Task icon"
          className="rounded img-fluid"
          style={{ width: "240px", height: "auto" }}
        />
        <div className="ms-3 d-flex flex-column align-items-start flex-grow-1">
          <p>Owner: {data.owner}</p>
          <p>This task is hidden</p>
        </div>
      </div>
    );
  }
  return (
    <Link
      to={`/tasks/${id}?${searchParams.toString()}`}
      className="btn btn-dark text-light w-100 d-flex overflow-hidden my-2 p-3 align-items-center"
    >
      <img
        src={`${import.meta.env.VITE_API_URL}/${localStorage.getItem("token")}/videos/${JSON.parse(data.videos)[0]}/thumbnail`}
        alt="Traveler"
        className="rounded img-fluid"
        style={{ width: "240px", height: "auto" }}
      />
      <div className="ms-3 d-flex flex-column align-items-start flex-grow-1">
        <h5>{data.title}</h5>
        {content}
        {progress_bar}
      </div>
    </Link>
  );
}

export default TaskComponent;
