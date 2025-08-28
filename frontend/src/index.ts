import React from 'react';
import ReactDOM from 'react-dom';
import App from '../packages/app/src/App';

const container = document.getElementById('root');
if (container) {
  ReactDOM.render(React.createElement(App), container);
} else {
  console.error('Root element not found');
}