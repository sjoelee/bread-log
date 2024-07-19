import Link from "./Link";

function Sidebar() {
  const [year, month, day, dough] = window.location.pathname.split('/').slice(1,5);
  // it should be directing to the make and bake of the dough for that day.

  const links = [
    { label: 'Make', path: `/${year}/${month}/${day}/${dough}/make`},
    { label: 'Bake', path: `/${year}/${month}/${day}/${dough}/bake`},
  ];

  const renderedLinks = links.map((link) => {
    return (
      <Link
        key={link.label}
        to={link.path}
        className="mb-3"
        activeClassName="font-bold border-l-4 border-blue-500 pl-2"
      >
        {link.label}
      </Link>
    );
  });

  return (
    <div className="sticky top-0 overflow-y-scroll flex flex-col items-start">
      {renderedLinks}
    </div>
  );
}

export default Sidebar;