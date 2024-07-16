import React, { useState } from 'react';

function DoughMakePage({ date, doughLabel, doughValue }) {
  console.log("selected ", date, doughLabel, doughValue);
  const [steps, setSteps] = useState({
    autolyse: { time: '', temp: '' },
    addStarter: { time: '', temp: '' },
    pullDough: { time: '', temp: '' },
    preshape: { time: '', temp: '' },
    finalShape: { time: '', temp: '' },
    refrigerate: { time: '', temp: '' },
  });

  const handleInputChange = (step, field, value) => {
    setSteps((prevSteps) => ({
      ...prevSteps,
      [step]: { ...prevSteps[step], [field]: value },
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would typically send the data to your backend API
    console.log('Submitting:', { doughLabel, date, steps });
  };

  return (
    <div>
      <h2>{doughLabel} - Dough Make Page</h2>
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
              value={temp}
              onChange={(e) => handleInputChange(step, 'temp', e.target.value)}
              placeholder="Temperature"
            />
          </div>
        ))}
        <button type="submit">Save</button>
      </form>
    </div>
  );
}

export default DoughMakePage;