import { Link, useParams, useSearchParams } from "react-router-dom";
import { ChevronLeft } from "lucide-react";
import TaskComponentSelected from "../components/TaskComponentSelected";
import { useEffect, useState } from "react";
import { useProgressSocket } from "../useProgressSocket.ts";
import axios from "axios";

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
  current_process_video_count: number;
  process_eta: number;
  current_video_id: string;
}

function SelectedTask() {
  const [searchParams] = useSearchParams();
  const { id } = useParams();
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
      <>
        <div className="bg-darker rounded text-light w-100 min-h-100 d-flex flex-column overflow-hidden p-4">
          <p>Something went wrong.</p>
          <p>Error: {error}</p>
        </div>
      </>
    );
  }

  if (!data) {
    return (
      <>
        <div className="bg-darker rounded text-light w-100 min-h-100 d-flex flex-column overflow-hidden p-4">
          <p>Loading...</p>
        </div>
      </>
    );
  }

  let content;
  if (data.type == "video") {
    content = (
      <>
        <p className="mb-0 my-1">Type: Video</p>
        <p className="mb-2 my-1">Videos: {JSON.parse(data.videos).length}</p>
      </>
    );
  } else {
    content = (
      <>
        <p className="mb-0 my-1">Type: Playlist</p>
        <p className="mb-2 my-1">Playlist: {data.playlist}</p>
      </>
    );
  }

  let progress_bar = (
    <>
      <p className="text-danger mb-1 mt-2">Disconnected</p>
      <div
        className="progress rounded-pill"
        style={{ height: "1.25rem", width: "100%" }}
      >
        <div
          className="progress-bar bg-success rounded-pill"
          role="progressbar"
          style={{
            width: `0%`,
          }}
          aria-valuenow={0}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          {"Waiting for other tasks 0%"}%
        </div>
      </div>
    </>
  );

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
        <div>
          {connected ? (
            <p className="text-success mb-1 mt-2">Connected</p>
          ) : (
            <p className="text-danger mb-1 mt-2">Disconnected</p>
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

  return (
    <>
      <div className="bg-darker rounded text-light w-100 min-h-100 d-flex overflow-hidden p-4">
        <div>
          <div>
            <Link
              to={`/tasks?${searchParams.toString()}`}
              className="btn btn-darker mb-1"
            >
              <ChevronLeft size={22} color={"Grey"} className="m-0 p-0" />
            </Link>
          </div>
          <div>
            <h1 className="mb-3">
              {data.title.length > 40
                ? data.title.slice(0, 40) + "..."
                : data.title}
            </h1>
            <p className="fw-bold">Selected Task: {id}</p>
            {content}
            <img
              src={`${import.meta.env.VITE_API_URL}/${localStorage.getItem("token")}/videos/${JSON.parse(data.videos)[0]}/thumbnail`}
              alt="Traveler"
              className="rounded img-fluid mb-3"
              style={{ width: "960px", height: "auto" }}
            />
            {progress_bar}
          </div>
        </div>
        <div className="ms-4 d-flex flex-column align-items-start flex-grow-1 ms-5 mt-5">
          {JSON.parse(data.videos).map((item: string) => (
            <TaskComponentSelected videoID={item} key={item} />
          ))}
        </div>
      </div>
    </>
  );
}

export default SelectedTask;
