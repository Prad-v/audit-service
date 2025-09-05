import React from 'react';
import MCPClient from '../components/MCPClient';

const MCPQuery: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Ask Me</h1>
        <p className="text-gray-600">
          Interact with the FastMCP server to query audit events using natural language. 
          Ask questions about events, trends, analytics, and alerts in a conversational way.
        </p>
      </div>

      <div className="h-[600px]">
        <MCPClient />
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-3">About FastMCP</h2>
        <p className="text-blue-800 mb-4">
          This interface uses the Model Context Protocol (MCP) to provide intelligent 
          natural language querying capabilities for audit events. The FastMCP server 
          understands context and can process complex queries about your audit data.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium text-blue-900 mb-2">Example Queries</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• "Show me all login events from today"</li>
              <li>• "How many failed authentication attempts in the last hour?"</li>
              <li>• "Get high severity events from the API service"</li>
              <li>• "Show me trends in user activity over the past week"</li>
              <li>• "What are the recent security alerts?"</li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-medium text-blue-900 mb-2">Features</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Natural language processing</li>
              <li>• Context-aware queries</li>
              <li>• Real-time responses</li>
              <li>• Structured data output</li>
              <li>• Error handling and validation</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MCPQuery;
