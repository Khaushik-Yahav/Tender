import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Layout Components
import Navbar from './components/Layout/Navbar';
import Sidebar from './components/Layout/Sidebar';
import Footer from './components/Layout/Footer';

// Page Components  
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Evaluation from './pages/Evaluation';
import Chat from './pages/Chat';
import Reports from './pages/Reports';

// Styles
import './styles/globals.css';
import './styles/components.css';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App d-flex flex-column min-vh-100">
          <Navbar />
          
          <div className="container-fluid flex-grow-1">
            <div className="row h-100">
              {/* Sidebar */}
              <div className="col-md-2 col-lg-2 p-0">
                <Sidebar />
              </div>
              
              {/* Main Content */}
              <div className="col-md-10 col-lg-10 p-4">
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/documents" element={<Documents />} />
                  <Route path="/evaluation" element={<Evaluation />} />
                  <Route path="/chat" element={<Chat />} />
                  <Route path="/reports" element={<Reports />} />
                </Routes>
              </div>
            </div>
          </div>
          
          <Footer />
          
          {/* Toast notifications */}
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
