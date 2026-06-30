import { Settings } from "lucide-react";

function ListGroup({ items }) {
  return (
    <>
      <div className="">
        <ul className="list-group gap-1 py-1">
          {items.map((item) => (
            <div>
              <Settings size={18} />
              <li key={item} className="btn btn-darker px-3">
                {item}
              </li>
            </div>
          ))}
        </ul>
      </div>
    </>
  );
}

export default ListGroup;
