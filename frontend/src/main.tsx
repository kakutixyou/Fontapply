// webforge-ai-desktop/frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// ※グローバルCSSのインポートは App.tsx 側で行っているため、ここでは省略しています。
// もし App.tsx からCSSのimportを消した場合は、ここに書いてください。

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);