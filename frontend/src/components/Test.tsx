import { useEffect, useState } from "react";

function Test() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/`)
      .then((res) => res.json())
      .then(setData);
  }, []);

  let text;

  if (data != null) {
    text = data["message"];
  }

  return <p>{text}</p>;
}

export default Test;
