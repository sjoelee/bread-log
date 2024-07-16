import { createContext, useContext, useState } from 'react';
import { useLocation } from 'wouter';

const NavigationContext = createContext();

export const NavigationProvider = ({ children }) => {
  const [location, setLocation] = useLocation();
  const [history, setHistory] = useState([]);

  const addToHistory = (path) => {
    setHistory((prevHistory) => [...prevHistory, path]);
  };

  const navigate = (to) => {
    setLocation(to);
    addToHistory(to);
  };

  const value = {
    navigate,
    history,
    location,
  };

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
};

export const useNavigation = () => {
  return useContext(NavigationContext);
};