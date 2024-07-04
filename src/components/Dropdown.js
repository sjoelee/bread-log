import { useEffect, useRef, useState } from 'react';
import useNavigation from '../hooks/use-navigation';
import { GoChevronDown } from "react-icons/go";
import Panel from './Panel';

function Dropdown({ selected, items, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);
  const divEl = useRef();
  const { navigate } = useNavigation();

  useEffect(() => {
    const handler = (event) => {
      if(!divEl.current) { //no reference to the element, do an early return
        return;
      }
      if (!divEl.current.contains(event.target)) {
        setIsOpen(false);
      }
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
    navigate(item.value)
  };

  const renderedItems = items.map((item) => {
    return (
      <div
        className="hover:bg-sky-100 rounded cursor-pointer p-1"
        key={item.label}
        onClick={() => handleItemSelect(item)}
      >
        {item.label}
      </div>
    );
  });

  return (
    <div ref={divEl} className='w-48 relative'>
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