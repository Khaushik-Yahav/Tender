import React, { useState, useRef, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, InputGroup, Badge } from 'react-bootstrap';
import { useMutation } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: 'Hello! I\'m your AI assistant for tender evaluation. I can help you with questions about uploaded documents, evaluation criteria, and tender processes. What would you like to know?',
      timestamp: new Date()
    }
  ]);
  
  const [message, setMessage] = useState('');
  const [tenderId, setTenderId] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const askQuestionMutation = useMutation({
    mutationFn: apiService.askQuestion,
    onSuccess: (data) => {
      if (data.status === 'success') {
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.data.answer,
          timestamp: new Date(),
          contextUsed: data.data.context_used,
          contextChunks: data.data.context_chunks_count
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        toast.error('Failed to get response from AI assistant');
      }
    },
    onError: () => {
      toast.error('Error communicating with AI assistant');
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !askQuestionMutation.isLoading) {
      // Add user message
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: message.trim(),
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, userMessage]);
      
      // Send to API
      askQuestionMutation.mutate({
        question: message.trim(),
        tender_id: tenderId || null,
        include_context: true
      });
      
      setMessage('');
    }
  };

  const handleSampleQuestion = (question) => {
    setMessage(question);
  };

  const sampleQuestions = [
    "What is the submission deadline for this tender?",
    "What are the mandatory technical requirements?",
    "How many vendors have submitted proposals?",
    "What is the estimated project value?",
    "What are the evaluation criteria and weights?"
  ];

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <h2 className="mb-1">AI Assistant</h2>
          <p className="text-muted mb-0">
            Ask questions about your documents and get intelligent responses
          </p>
        </Col>
      </Row>

      <Row>
        <Col lg={8}>
          <Card className="border-0 shadow-sm" style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
            {/* Chat Messages */}
            <Card.Body className="flex-grow-1 overflow-auto p-0">
              <div className="p-3" style={{ minHeight: '100%', backgroundColor: '#f8f9fa' }}>
                {messages.map((msg) => (
                  <div key={msg.id} className={`d-flex mb-3 ${msg.type === 'user' ? 'justify-content-end' : 'justify-content-start'}`}>
                    <div 
                      className={`rounded-3 p-3 ${
                        msg.type === 'user' 
                          ? 'bg-primary text-white ms-5' 
                          : 'bg-white border me-5'
                      }`}
                      style={{ maxWidth: '70%' }}
                    >
                      {msg.type === 'assistant' && (
                        <div className="d-flex align-items-center mb-2">
                          <i className="fas fa-robot text-primary me-2"></i>
                          <small className="text-muted fw-medium">AI Assistant</small>
                        </div>
                      )}
                      
                      <div className="message-content">
                        {msg.content}
                      </div>
                      
                      <div className="mt-2 d-flex align-items-center justify-content-between">
                        <small className={msg.type === 'user' ? 'text-light opacity-75' : 'text-muted'}>
                          {formatDistanceToNow(msg.timestamp, { addSuffix: true })}
                        </small>
                        
                        {msg.type === 'assistant' && msg.contextUsed && (
                          <Badge bg="light" text="dark" className="ms-2">
                            <i className="fas fa-database me-1"></i>
                            {msg.contextChunks} sources
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                
                {askQuestionMutation.isLoading && (
                  <div className="d-flex justify-content-start mb-3">
                    <div className="bg-white border rounded-3 p-3 me-5">
                      <div className="d-flex align-items-center">
                        <div className="spinner-border spinner-border-sm text-primary me-2" role="status">
                          <span className="visually-hidden">Loading...</span>
                        </div>
                        <small className="text-muted">AI is thinking...</small>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </Card.Body>
            
            {/* Chat Input */}
            <Card.Footer className="bg-white">
              <Form onSubmit={handleSubmit}>
                <div className="d-flex align-items-center mb-2">
                  <Form.Control
                    type="text"
                    size="sm"
                    placeholder="Tender ID (optional)"
                    value={tenderId}
                    onChange={(e) => setTenderId(e.target.value)}
                    style={{ maxWidth: '200px' }}
                    className="me-2"
                  />
                  <small className="text-muted">
                    Specify tender ID for more relevant responses
                  </small>
                </div>
                
                <InputGroup>
                  <Form.Control
                    as="textarea"
                    rows={2}
                    placeholder="Ask me anything about your tender documents..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(e);
                      }
                    }}
                    disabled={askQuestionMutation.isLoading}
                    style={{ resize: 'none' }}
                  />
                  <Button 
                    variant="primary" 
                    type="submit" 
                    disabled={askQuestionMutation.isLoading || !message.trim()}
                    className="px-4"
                  >
                    {askQuestionMutation.isLoading ? (
                      <i className="fas fa-spinner fa-spin"></i>
                    ) : (
                      <i className="fas fa-paper-plane"></i>
                    )}
                  </Button>
                </InputGroup>
                
                <div className="d-flex justify-content-between align-items-center mt-2">
                  <small className="text-muted">
                    Press Enter to send, Shift+Enter for new line
                  </small>
                </div>
              </Form>
            </Card.Footer>
          </Card>
        </Col>
        
        <Col lg={4}>
          <Card className="border-0 shadow-sm mb-3">
            <Card.Header className="bg-white">
              <Card.Title className="h6 mb-0">
                <i className="fas fa-lightbulb text-warning me-2"></i>
                Sample Questions
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="d-grid gap-2">
                {sampleQuestions.map((question, index) => (
                  <Button
                    key={index}
                    variant="outline-secondary"
                    size="sm"
                    className="text-start"
                    onClick={() => handleSampleQuestion(question)}
                    disabled={askQuestionMutation.isLoading}
                  >
                    <small>{question}</small>
                  </Button>
                ))}
              </div>
            </Card.Body>
          </Card>

          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-white">
              <Card.Title className="h6 mb-0">
                <i className="fas fa-info-circle text-info me-2"></i>
                Tips for Better Results
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <ul className="list-unstyled mb-0 small">
                <li className="mb-2">
                  <i className="fas fa-check text-success me-2"></i>
                  Be specific with your questions
                </li>
                <li className="mb-2">
                  <i className="fas fa-check text-success me-2"></i>
                  Reference specific tender numbers or vendor names
                </li>
                <li className="mb-2">
                  <i className="fas fa-check text-success me-2"></i>
                  Ask about compliance, requirements, or evaluation criteria
                </li>
                <li>
                  <i className="fas fa-check text-success me-2"></i>
                  Upload relevant documents first for better context
                </li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Chat;
