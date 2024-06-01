import Dropdown from "./components/Dropdown";
import DoughMakePage from "./components/DoughMakePage";
import Link from './components/Link';
import Route from './components/Route';
import { useState } from "react";

function App() {
  const [selected, setSelected] = useState(null);
  const onSelect = (item) => {
    setSelected(item);
  }
  const doughMakes = [
    {label: 'Team Make A', value: 'team_a'},
    {label: 'Team Make B', value: 'team_b'},
    {label: 'Team Make C', value: 'team_c'},
    {label: 'Ube', value: 'ube'},
    {label: 'Demi Baguette', value: 'demi'},
    {label: 'Hoagies A', value: 'hoagie_a'},
    {label: 'Hoagies B', value: 'hoagie_b'},
    {label: 'Ciaboutty', value: 'ciaboutty'},
  ]
  return(
    <div>
      <Dropdown items={ doughMakes } onSelect={ onSelect } selected={ selected }/>
      <Link to="/accordion">Go to accordion</Link>
      <Link to="/make">Go to dropdown</Link>
      <div>
        <Route path="/make">
          <DoughMakePage makeName={ selected }/>
        </Route>
      </div>
    </div>
  );
}

export default App;