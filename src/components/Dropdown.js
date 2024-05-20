import { useState } from 'react';
function Dropdown({ selected, items, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);

  const handleClick = () => {
    setIsOpen(!isOpen);
  };

  const handleSelect = (item) => {
    setIsOpen(false);
    onSelect(item);
  };

  const renderedItems = items.map((item) => {
    return (<div key={item.label} onClick={() => handleSelect(item)}>
      {item.label}
    </div>);
  });

  return (
    <div onClick={handleClick}>
      {(isOpen && renderedItems) || selected?.label || 'Select Make'}
    </div>
  );
}

export default Dropdown;