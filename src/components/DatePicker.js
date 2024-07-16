import React from 'react';

function DatePicker({ date, onDateChange }) {
  const handleDateChange = (e) => {
    onDateChange(new Date(e.target.value));
  };

  return (
    <input
      type="date"
      value={date.toISOString().split('T')[0]}
      onChange={handleDateChange}
    />
  );
}

export default DatePicker;