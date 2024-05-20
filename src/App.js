import Dropdown from "./components/Dropdown";
import { useState } from "react";

function App() {
  const [selected, setSelected] = useState(null);
  const onSelect = (item) => {
    setSelected(item);
  }
  console.log('app selection: ', selected);
  const doughMakes = [
    {label: 'Team Make #1', value: 'team_1'},
    {label: 'Team Make #2', value: 'team_2'},
    {label: 'Ube', value: 'ube'},
    {label: 'Demi Baguette', value: 'demi'},
    {label: 'Hoagies #1', value: 'hoagie_1'},
    {label: 'Hoagies #2', value: 'hoagie_2'},
    {label: 'Ciaboutty', value: 'ciaboutty'},
  ]
  return(
    <div>
      <Dropdown items={ doughMakes } onSelect={ onSelect } selected={ selected }/>
    </div>
  );
}

export default App;