import { useState } from 'react';
import { GoChevronDown } from "react-icons/go";

function Dropdown({ selected, items, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);

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
      <div className="flex justify-between items-center cursor-pointer border rounded p-3 shadow bg-white w-full" onClick={handleClick}>
        {selected?.label || 'Select Make'}
        <GoChevronDown className="text-lg"/>
      </div>
      {isOpen && (
        <div className="absolute top-full border rounded p-3 shadow bg-white w-full">
          {renderedItems}
        </div>
      )}
    </div>
  );
}

export default Dropdown;