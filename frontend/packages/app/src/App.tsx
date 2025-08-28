import React from 'react';

const App = () => {
  const [currentPage, setCurrentPage] = React.useState('home');

  const HomePage = () => (
    <div style={{ padding: '20px' }}>
      <h2>Welcome to Audit Log Framework</h2>
      <p>This is the home page of the Audit Log Framework.</p>
      <nav>
        <ul>
          <li>
            <button
              onClick={() => setCurrentPage('audit-logs')}
              style={{
                background: '#007bff',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              View Audit Logs
            </button>
          </li>
        </ul>
      </nav>
    </div>
  );

  const AuditLogPage = () => (
    <div style={{ padding: '20px' }}>
      <h2>Audit Log Page</h2>
      <p>Audit Log functionality is coming soon!</p>
      <nav>
        <ul>
          <li>
            <button
              onClick={() => setCurrentPage('home')}
              style={{
                background: '#6c757d',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              Back to Home
            </button>
          </li>
        </ul>
      </nav>
    </div>
  );

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{
        color: '#333',
        borderBottom: '2px solid #007bff',
        paddingBottom: '10px',
        marginBottom: '20px'
      }}>
        Audit Log Framework
      </h1>
      {currentPage === 'home' && <HomePage />}
      {currentPage === 'audit-logs' && <AuditLogPage />}
    </div>
  );
};

export default App;