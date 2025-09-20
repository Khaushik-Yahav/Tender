import React from 'react';
import { Navbar as BSNavbar, Nav, Container, Badge } from 'react-bootstrap';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../../services/api';

const Navbar = () => {
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: apiService.healthCheck,
    refetchInterval: 30000, // Check health every 30 seconds
  });

  const isHealthy = healthData?.data?.status === 'success';

  return (
    <BSNavbar bg="primary" variant="dark" expand="lg" className="shadow-sm">
      <Container fluid>
        <BSNavbar.Brand href="/dashboard" className="fw-bold">
          <i className="fas fa-file-contract me-2"></i>
          Tender Evaluation System
        </BSNavbar.Brand>
        
        <BSNavbar.Toggle aria-controls="basic-navbar-nav" />
        <BSNavbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto align-items-center">
            {/* System Status */}
            <Nav.Item className="me-3">
              <Badge bg={isHealthy ? 'success' : 'danger'} className="d-flex align-items-center">
                <i className={`fas fa-circle me-1 ${isHealthy ? 'text-light' : 'text-white'}`}></i>
                {isHealthy ? 'System Online' : 'System Offline'}
              </Badge>
            </Nav.Item>
            
            {/* User Menu */}
            <Nav.Item>
              <div className="dropdown">
                <button 
                  className="btn btn-outline-light btn-sm dropdown-toggle" 
                  type="button" 
                  data-bs-toggle="dropdown"
                >
                  <i className="fas fa-user me-1"></i>
                  Admin User
                </button>
                <ul className="dropdown-menu dropdown-menu-end">
                  <li><a className="dropdown-item" href="#profile">Profile</a></li>
                  <li><a className="dropdown-item" href="#settings">Settings</a></li>
                  <li><hr className="dropdown-divider" /></li>
                  <li><a className="dropdown-item" href="#logout">Logout</a></li>
                </ul>
              </div>
            </Nav.Item>
          </Nav>
        </BSNavbar.Collapse>
      </Container>
    </BSNavbar>
  );
};

export default Navbar;
