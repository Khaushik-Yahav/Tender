import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Table, Badge } from 'react-bootstrap';

const Reports = () => {
  const [selectedReport, setSelectedReport] = useState('evaluation');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  const reportTypes = [
    {
      id: 'evaluation',
      title: 'Vendor Evaluation Report',
      description: 'Comprehensive evaluation results for all vendors',
      icon: 'fas fa-chart-bar'
    },
    {
      id: 'comparison',
      title: 'Vendor Comparison Report', 
      description: 'Side-by-side comparison of vendor proposals',
      icon: 'fas fa-balance-scale'
    },
    {
      id: 'compliance',
      title: 'Compliance Analysis Report',
      description: 'Detailed compliance analysis for tender requirements',
      icon: 'fas fa-check-circle'
    },
    {
      id: 'summary',
      title: 'Executive Summary',
      description: 'High-level summary for decision makers',
      icon: 'fas fa-file-alt'
    }
  ];

  const mockReports = [
    {
      id: 1,
      name: 'Q4 2024 Vendor Evaluation',
      type: 'Evaluation Report',
      date: '2024-12-15',
      status: 'Completed',
      size: '2.3 MB'
    },
    {
      id: 2,
      name: 'Software Development RFP Analysis',
      type: 'Compliance Analysis',
      date: '2024-12-10',
      status: 'Completed',
      size: '1.8 MB'
    },
    {
      id: 3,
      name: 'Vendor Comparison - TechCorp vs ABC',
      type: 'Comparison Report',
      date: '2024-12-08',
      status: 'Draft',
      size: '3.1 MB'
    }
  ];

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <h2 className="mb-1">Reports & Analytics</h2>
          <p className="text-muted mb-0">
            Generate comprehensive reports and analytics for tender evaluations
          </p>
        </Col>
      </Row>

      <Row>
        <Col lg={4}>
          <Card className="border-0 shadow-sm mb-4">
            <Card.Header className="bg-white">
              <Card.Title className="h6 mb-0">
                <i className="fas fa-plus text-primary me-2"></i>
                Generate New Report
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <Form>
                <Form.Group className="mb-3">
                  <Form.Label>Report Type</Form.Label>
                  <Form.Select 
                    value={selectedReport} 
                    onChange={(e) => setSelectedReport(e.target.value)}
                  >
                    {reportTypes.map(type => (
                      <option key={type.id} value={type.id}>
                        {type.title}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Date Range</Form.Label>
                  <Row>
                    <Col>
                      <Form.Control 
                        type="date" 
                        placeholder="Start Date"
                        value={dateRange.start}
                        onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                      />
                    </Col>
                    <Col>
                      <Form.Control 
                        type="date" 
                        placeholder="End Date"
                        value={dateRange.end}
                        onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                      />
                    </Col>
                  </Row>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Output Format</Form.Label>
                  <div>
                    <Form.Check 
                      inline 
                      type="radio" 
                      name="format" 
                      id="pdf" 
                      label="PDF" 
                      defaultChecked 
                    />
                    <Form.Check 
                      inline 
                      type="radio" 
                      name="format" 
                      id="excel" 
                      label="Excel" 
                    />
                    <Form.Check 
                      inline 
                      type="radio" 
                      name="format" 
                      id="word" 
                      label="Word" 
                    />
                  </div>
                </Form.Group>

                <Button variant="primary" className="w-100">
                  <i className="fas fa-download me-2"></i>
                  Generate Report
                </Button>
              </Form>
            </Card.Body>
          </Card>

          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-white">
              <Card.Title className="h6 mb-0">
                <i className="fas fa-chart-pie text-warning me-2"></i>
                Analytics Overview
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={6} className="text-center mb-3">
                  <h3 className="text-primary">24</h3>
                  <small className="text-muted">Total Reports</small>
                </Col>
                <Col md={6} className="text-center mb-3">
                  <h3 className="text-success">18</h3>
                  <small className="text-muted">Completed</small>
                </Col>
                <Col md={6} className="text-center mb-3">
                  <h3 className="text-warning">4</h3>
                  <small className="text-muted">In Progress</small>
                </Col>
                <Col md={6} className="text-center mb-3">
                  <h3 className="text-info">2</h3>
                  <small className="text-muted">Drafts</small>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={8}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-white d-flex justify-content-between align-items-center">
              <Card.Title className="h6 mb-0">
                <i className="fas fa-history text-secondary me-2"></i>
                Recent Reports
              </Card.Title>
              <Button variant="outline-secondary" size="sm">
                <i className="fas fa-sync me-1"></i>
                Refresh
              </Button>
            </Card.Header>
            <Card.Body className="p-0">
              <Table responsive hover className="mb-0">
                <thead className="bg-light">
                  <tr>
                    <th>Report Name</th>
                    <th>Type</th>
                    <th>Date Created</th>
                    <th>Status</th>
                    <th>Size</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {mockReports.map(report => (
                    <tr key={report.id}>
                      <td className="fw-medium">{report.name}</td>
                      <td>{report.type}</td>
                      <td>{new Date(report.date).toLocaleDateString()}</td>
                      <td>
                        <Badge bg={report.status === 'Completed' ? 'success' : 'warning'}>
                          {report.status}
                        </Badge>
                      </td>
                      <td>{report.size}</td>
                      <td>
                        <div className="btn-group btn-group-sm">
                          <Button variant="outline-primary" size="sm" title="View">
                            <i className="fas fa-eye"></i>
                          </Button>
                          <Button variant="outline-success" size="sm" title="Download">
                            <i className="fas fa-download"></i>
                          </Button>
                          <Button variant="outline-danger" size="sm" title="Delete">
                            <i className="fas fa-trash"></i>
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Reports;

