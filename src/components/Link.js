import { useContext } from 'react';
import NavigationContext from "../context/navigation";

function Link({ to, children }) {
  const { navigate } = useContext(NavigationContext);
  const handleClick = (event) => {
    event.preventDefault(); // prevent it from doing the default behavior.

    navigate(to);
  };

  return <a onClick={handleClick}>{children}</a>
}

export default Link;