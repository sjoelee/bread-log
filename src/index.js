import './index.css';
import React from 'react';
import ReactDOM from 'react-dom/client';
import BreadApp from './BreadApp.tsx';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { NavigationProvider } from './context/navigation';
import { LocalizationProvider } from '@mui/x-date-pickers';

const el = document.getElementById('root');
const root = ReactDOM.createRoot(el);

root.render(
  <NavigationProvider>
    <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale='en'>
      <BreadApp/>
    </LocalizationProvider>
  </NavigationProvider>
);