import { useEffect, useState } from "react";
import axios from "axios";
import TaskComponent from "../components/TaskComponent.tsx";
import { SquarePenIcon } from "lucide-react";
import { Link } from "react-router-dom";

interface ApiResponse {
  process: string[];
}

function Tasks() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [shownTask, setShownTask] = useState<boolean | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_URL}/process`,
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
        <div className="d-flex justify-content-start align-items-end justify-content-end w-100">
          <Link
            to="/tasks/create"
            className="btn btn-dark text-light d-flex overflow-hidden my-2 p-3 align-items-center"
          >
            <SquarePenIcon />
            <p className="mb-0 ms-2">Create</p>
          </Link>
        </div>
        {data.process.map((item) => (
          <TaskComponent id={item} key={item} set={setShownTask} />
        ))}

        {!shownTask ? (
          <div className="d-flex flex-grow-1 align-items-start w-100 px-2">
            <p>All tasks finished... Press create to create one.</p>
          </div>
        ) : null}
      </div>
    </>
  );
}

export default Tasks;
