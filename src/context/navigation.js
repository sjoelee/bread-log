import { createContext, useState, useEffect } from "react";

const NavigationContext = createContext();

function NavigationProvider({ children }) {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    // sets currentpath whenever the user clicks the back and forth button.
    const handler = () => {
      setCurrentPath(window.location.pathname)
    };
    window.addEventListener('popstate', handler);

    return () => {
      window.removeEventListener('popstate', handler);
    };
  }, []);

  const navigate = (to) => {
    window.history.pushState({}, '', to);
    setCurrentPath(to);
  }

  return (
    <NavigationContext.Provider value={{ currentPath, navigate }}>
      {currentPath}
      {children}
    </NavigationContext.Provider>
  );
}

export { NavigationProvider };
export default NavigationContext;

// By using NavigationContext and NavigationProvider, you encapsulate navigation logic and make it reusable across your application, leading to a cleaner and more maintainable codebase.