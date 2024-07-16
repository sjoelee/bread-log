import DatePicker from "./components/DatePicker";
import Dropdown from "./components/Dropdown";
import DoughMakePage from "./page/DoughMakePage";
import DoughBakePage from "./page/DoughBakePage";
import Sidebar from "./components/Sidebar";
import { useState } from "react";
import { Route, Switch } from 'wouter';
import { NavigationProvider } from './components/NavigationProvider';

function App() {
  const [date, setDate] = useState(new Date());
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

  return (
    <NavigationProvider>
      <div className="container mx-auto grid grid-cols-4 gap-4 mt-4 relative">
        <div className="col-span-1 space-y-4">
          <div className="relative z-0">
            <DatePicker date={date} onDateChange={setDate} />
          </div>
          <div className="relative z-10">
            <Dropdown items={doughMakes} onSelect={onSelect} selected={selected} />
          </div>
          <div className="relative z-0">
            <Sidebar />
          </div>
        </div>
        <div className="col-span-3">
          <Switch>
            <Route path="/:selected/make">
              {(params) => {
                const selected = params.selected;
                const selectedDough = doughMakes.find(item => item.value === selected);

                return (
                  <DoughMakePage doughLabel={selectedDough.label} doughValue={selectedDough.value} />
                );
              }}
            </Route>
            <Route path="/:selected/bake" component={DoughBakePage} />
          </Switch>
        </div>
      </div>
    </NavigationProvider>
  );
}

export default App;