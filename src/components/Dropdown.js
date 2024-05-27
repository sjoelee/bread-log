import { useEffect, useState } from 'react';
import { GoChevronDown } from "react-icons/go";
import Panel from './Panel';

function Dropdown({ selected, items, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handler = (event) => {
      console.log(event);
    };

    document.addEventListener('click', handler, true);

    return () => {
      document.removeEventListener('click', handler);
    };
  }, []);

  const handleClick = () => {
    setIsOpen(!isOpen);
  };

  const handleItemSelect = (item) => {
    setIsOpen(false);
    onSelect(item);
  };

  const renderedItems = items.map((item) => {
    return (<div className="hover:bg-sky-100 rounded cursor-pointer p-1" key={item.label} onClick={() => handleItemSelect(item)}>
      {item.label}
    </div>);
  });

  return (
    <div className='w-48 relative'>
      <Panel
        className="flex justify-between items-center cursor-pointer"
        onClick={handleClick}
      >
        {selected?.label || 'Select Make'}
        <GoChevronDown className="text-lg"/>
      </Panel>
      {isOpen && (
        <Panel 
          className="absolute top-full"
        >
          {renderedItems}
        </Panel>
      )}
    </div>
  );
}

export default Dropdown;