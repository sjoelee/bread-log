import React from 'react';

function DatePicker({ date, onDateChange }) {
  // Date picked is midnight with respect to UTC and we need that in our local time zone. 
  // Adjust the date to account for timezone differences between local and UTC. Once adjusted the date should be midnight in our local time zone.
  const handleDateChange = (e) => {
    const selectedDate = new Date(e.target.value);
    const timezoneOffset = selectedDate.getTimezoneOffset() * 60 * 1000; // convert minutes to milliseconds, UTC to PST.
    const adjustedDate = new Date(selectedDate.getTime() + timezoneOffset);
    onDateChange(adjustedDate);
  };

  const formatDateForInput = (date) => {
    const offset = date.getTimezoneOffset();
    const adjustedDate = new Date(date.getTime() - (offset * 60 * 1000)); //convert minutes to milliseconds, PST to UTC. 
    return adjustedDate.toISOString().split('T')[0];
  };

  return (
    <input
      type="date"
      value={formatDateForInput(date)}
      onChange={handleDateChange}
    />
  );
}

export default DatePicker;