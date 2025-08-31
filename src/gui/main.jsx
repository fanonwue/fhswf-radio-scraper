import React from 'react';
import { createRoot } from 'react-dom/client';
import RadioSummaryApp from './RadioSummaryApp.jsx';

const root = createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <RadioSummaryApp />
  </React.StrictMode>
);
