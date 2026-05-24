import React from 'react';
import { Dashboard } from './components/Dashboard';

const API_BASE = 'http://101.43.54.229:8080';

function App() {
  return (
    <div className="App">
      <Dashboard apiBase={API_BASE} />
    </div>
  );
}

export default App;
