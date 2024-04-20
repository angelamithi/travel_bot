import React, { useState, useEffect } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import './App.css';

// Connect to the server where your Flask app is running
const socket = io('http://localhost:5000');  // Change the port if your Flask app is running on a different one

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');

  useEffect(() => {
    // Listen for real-time updates
    socket.on('update', data => {
      console.log(data.status);  // Or handle it in a more advanced way, like displaying a notification
      addMessage('bot', data.status);  // Display status updates in the chat window
    });

    return () => {
      socket.off('update');  // Cleanup on unmount
    };
  }, []);

  const handleInputChange = (e) => {
    setInputText(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const userMessage = inputText.trim();
    if (!userMessage) return;
    addMessage('user', userMessage);

    try {
      const response = await axios.post('/chat', { message: userMessage });
      addMessage('bot', response.data.reply);
    } catch (error) {
      console.error('Error responding from bot:', error);
      addMessage('bot', 'Sorry, there was an error communicating with Tara.');
    }
    setInputText('');
  };

  const addMessage = (sender, text) => {
    setMessages(messages => [...messages, { sender, text }]);
  };

  return (
    <div className="App">
      <h1>Tara the Travel Mate</h1>
      <div className="chat-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <div className="message-content">{msg.text}</div>
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={inputText}
          onChange={handleInputChange}
          placeholder="Ask Tara..."
          autoFocus
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}

export default App;
