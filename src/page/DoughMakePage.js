import React, { useState } from 'react';

function DoughMakePage({ doughType }) {
  const [date, setDate] = useState(new Date());
  const [isCelsius, setIsCelsius] = useState(false); // Default to Fahrenheit
  const [steps, setSteps] = useState({
    autolyse: { time: '', temp: 68 },     // 20°C in °F
    addStarter: { time: '', temp: 68 },   // 20°C in °F
    pullDough: { time: '', temp: 68 },    // 20°C in °F
    preshape: { time: '', temp: 68 },     // 20°C in °F
    finalShape: { time: '', temp: 68 },   // 20°C in °F
    refrigerate: { time: '', temp: 39 },  // 4°C in °F
  });

  const handleInputChange = (step, field, value) => {
    setSteps((prevSteps) => ({
      ...prevSteps,
      [step]: { ...prevSteps[step], [field]: value },
    }));
  };

  const handleTempChange = (step, temp) => {
    const newTemp = isCelsius ? temp : Math.round((temp - 32) * 5 / 9);
    handleInputChange(step, 'temp', newTemp);
  };

  const toggleTempUnit = () => {
    setIsCelsius(!isCelsius);
    setSteps((prevSteps) => {
      const newSteps = { ...prevSteps };
      for (const step in newSteps) {
        newSteps[step].temp = isCelsius
          ? Math.round((newSteps[step].temp * 9) / 5 + 32)
          : Math.round(((newSteps[step].temp - 32) * 5) / 9);
      }
      return newSteps;
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Submitting:', { doughType, date, steps, tempUnit: isCelsius ? 'C' : 'F' });
  };

  return (
    <div>
      <h2>{doughType} - Dough Make Page</h2>
      <div>
        <label className="switch">
          <input
            type="checkbox"
            checked={isCelsius}
            onChange={toggleTempUnit}
          />
          <span className="slider round"></span>
        </label>
        <span>{isCelsius ? 'Celsius' : 'Fahrenheit'}</span>
      </div>
      <form onSubmit={handleSubmit}>
        {Object.entries(steps).map(([step, { time, temp }]) => (
          <div key={step}>
            <h3>{step}</h3>
            <input
              type="time"
              value={time}
              onChange={(e) => handleInputChange(step, 'time', e.target.value)}
            />
            <input
              type="number"
              value={isCelsius ? temp : Math.round((temp * 9) / 5 + 32)}
              onChange={(e) => handleTempChange(step, parseInt(e.target.value))}
              min={isCelsius ? -20 : -4}
              max={isCelsius ? 100 : 212}
              step="1"
            />
            <span>{isCelsius ? '°C' : '°F'}</span>
          </div>
        ))}
        <button type="submit">Save</button>
      </form>
    </div>
  );
}

export default DoughMakePage;