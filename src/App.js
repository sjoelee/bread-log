import Dropdown from "./components/Dropdown";
import DoughMakePage from "./components/DoughMakePage";
import Link from './components/Link';
import Route from './components/Route';
import Sidebar from "./components/Sidebar";
import { useState } from "react";

function App() {
  const [selected, setSelected] = useState(null);
  const onSelect = (item) => {
    setSelected(item);
  }
  const doughMakes = [
    {label: 'Team Make A', value: 'team_a', path: './team_a'},
    {label: 'Team Make B', value: 'team_b', path: './team_b'},
    {label: 'Team Make C', value: 'team_c', path: './team_c'},
    {label: 'Ube', value: 'ube', path: './ube'},
    {label: 'Demi Baguette', value: 'demi', path: './demi'},
    {label: 'Hoagies A', value: 'hoagie_a', path: './hoagie_a'},
    {label: 'Hoagies B', value: 'hoagie_b', path: './hoagie_b'},
    {label: 'Ciaboutty', value: 'ciaboutty', path: './ciaboutty'},
  ]

  return(
    <div className="container mx-auto grid grid-cols-1 gap-4 mt-4 relative">
      <div className="z-10">
        <Dropdown items={doughMakes} onSelect={onSelect} selected={selected} />
      </div>
      <div className="z-0">
        <Sidebar />
      </div>
    </div>
  );
}

export default App;