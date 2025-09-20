import React from 'react';
import { Container, Row, Col, Card, Alert } from 'react-bootstrap';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';

const Dashboard = () => {
  const { 
    data: healthData, 
    isLoading: healthLoading 
  } = useQuery({
    queryKey: ['health'],
    queryFn: apiService.healthCheck
  });

  if (healthLoading) {
    return (
      <Container>
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </Container>
    );
  }

  return (
    <Container fluid>
      {/* Page Header */}
      <Row className="mb-4">
        <Col>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h2 className="mb-1">Dashboard</h2>
              <p className="text-muted mb-0">
                Welcome to the AI-powered tender evaluation system
              </p>
            </div>
            <div className="text-end">
              <small className="text-muted">
                Last updated: {new Date().toLocaleTimeString()}
              </small>
            </div>
          </div>
        </Col>
      </Row>

      {/* System Status Alert */}
      {healthData?.data?.status === 'success' && (
        <Row className="mb-4">
          <Col>
            <Alert variant="success" className="d-flex align-items-center">
              <i className="fas fa-check-circle me-2"></i>
              All systems operational. AI services are running smoothly.
            </Alert>
          </Col>
        </Row>
      )}

      {/* Quick Stats */}
      <Row className="mb-4">
        <Col lg={3} md={6} className="mb-3">
          <Card className="border-0 shadow-sm h-100">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="icon-circle bg-primary text-white me-3">
                  <i className="fas fa-file-alt"></i>
                </div>
                <div className="flex-grow-1">
                  <h3 className="mb-0">24</h3>
                  <p className="text-muted mb-0">Total Documents</p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={3} md={6} className="mb-3">
          <Card className="border-0 shadow-sm h-100">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="icon-circle bg-success text-white me-3">
                  <i className="fas fa-chart-line"></i>
                </div>
                <div className="flex-grow-1">
                  <h3 className="mb-0">8</h3>
                  <p className="text-muted mb-0">Evaluations</p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={3} md={6} className="mb-3">
          <Card className="border-0 shadow-sm h-100">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="icon-circle bg-warning text-white me-3">
                  <i className="fas fa-gavel"></i>
                </div>
                <div className="flex-grow-1">
                  <h3 className="mb-0">12</h3>
                  <p className="text-muted mb-0">Active Tenders</p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={3} md={6} className="mb-3">
          <Card className="border-0 shadow-sm h-100">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="icon-circle bg-info text-white me-3">
                  <i className="fas fa-server"></i>
                </div>
                <div className="flex-grow-1">
                  <h3 className="mb-0">99.9%</h3>
                  <p className="text-muted mb-0">System Uptime</p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Getting Started */}
      <Row>
        <Col>
          <Card className="border-0 shadow-sm">
            <Card.Body>
              <Card.Title className="h5">
                <i className="fas fa-info-circle text-primary me-2"></i>
                Getting Started
              </Card.Title>
              <Card.Text>
                <ol className="mb-0">
                  <li className="mb-2">
                    <strong>Upload Documents:</strong> Go to the Documents section to upload tender documents and vendor proposals.
                  </li>
                  <li className="mb-2">
                    <strong>Ask Questions:</strong> Use the AI Assistant to ask questions about your documents.
                  </li>
                  <li className="mb-2">
                    <strong>Evaluate Vendors:</strong> Navigate to Evaluation to assess vendor proposals against your criteria.
                  </li>
                  <li>
                    <strong>Generate Reports:</strong> Create comprehensive evaluation reports in the Reports section.
                  </li>
                </ol>
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard;
