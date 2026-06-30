import { useParams, useSearchParams } from "react-router-dom";

function TestId() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();

  const sidebar = searchParams.get("sidebar");

  return (
    <>
      <p>{id}</p>
      <p>{sidebar}</p>
    </>
  );
}

export default TestId;
