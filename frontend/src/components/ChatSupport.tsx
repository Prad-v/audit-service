import { useState, useRef, useEffect } from 'react'
import { MessageSquare, X, Send, Bot, User } from 'lucide-react'

interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
}

export function ChatSupport() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! I\'m your AI assistant. How can I help you with the audit service today?',
      sender: 'bot',
      timestamp: new Date()
    }
  ])
  const [inputText, setInputText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputText.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsTyping(true)

    // Simulate bot response (in a real implementation, this would call an API)
    setTimeout(() => {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: getBotResponse(inputText),
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, botResponse])
      setIsTyping(false)
    }, 1000)
  }

  const getBotResponse = (userInput: string): string => {
    const input = userInput.toLowerCase()
    
    if (input.includes('audit') || input.includes('log')) {
      return 'I can help you with audit logs! You can view, filter, and create audit events. Would you like to know more about specific audit log features?'
    }
    
    if (input.includes('incident') || input.includes('alert')) {
      return 'For incident management, you can view incidents, create alerts, and manage incident responses. Check the Incident Management tab for more details.'
    }
    
    if (input.includes('integration') || input.includes('jira') || input.includes('pagerduty')) {
      return 'I can help you configure integrations! Go to Settings > Integrations to set up Jira, PagerDuty, StackStorm, or Webhook integrations.'
    }
    
    if (input.includes('dashboard') || input.includes('overview')) {
      return 'The dashboard provides an overview of your system health, recent events, and key metrics. You can customize it to show the information most relevant to you.'
    }
    
    if (input.includes('help') || input.includes('support')) {
      return 'I\'m here to help! You can ask me about:\n• Audit logs and event management\n• Incident management and alerts\n• Integration setup\n• Dashboard features\n• General navigation\n\nWhat would you like to know more about?'
    }
    
    if (input.includes('settings') || input.includes('configure')) {
      return 'Settings allow you to configure:\n• Cloud projects and credentials\n• LLM providers for AI features\n• Third-party integrations\n• Feature flags\n• Application settings\n\nNavigate to the Settings tab to get started.'
    }
    
    return 'I understand you\'re asking about: "' + userInput + '". I can help you with audit logs, incident management, integrations, and general navigation. Could you be more specific about what you\'d like to know?'
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-colors z-50"
        aria-label="Open chat support"
      >
        {isOpen ? <X className="w-6 h-6" /> : <MessageSquare className="w-6 h-6" />}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-80 h-96 bg-white rounded-lg shadow-xl border border-gray-200 flex flex-col z-50">
          {/* Chat Header */}
          <div className="bg-blue-600 text-white p-4 rounded-t-lg flex items-center justify-between">
            <div className="flex items-center">
              <Bot className="w-5 h-5 mr-2" />
              <h3 className="font-semibold">Ask Me - AI Assistant</h3>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs px-3 py-2 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="flex items-start">
                    {message.sender === 'bot' && (
                      <Bot className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                    )}
                    {message.sender === 'user' && (
                      <User className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="text-sm whitespace-pre-wrap">{message.text}</div>
                  </div>
                  <div
                    className={`text-xs mt-1 ${
                      message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 px-3 py-2 rounded-lg">
                  <div className="flex items-center">
                    <Bot className="w-4 h-4 mr-2" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                disabled={isTyping}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputText.trim() || isTyping}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white p-2 rounded-md transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
