import React, { useState } from 'react';
import { Container, Row, Col, Tab, Tabs, Alert, Card, Form, Button, Table, Badge, ProgressBar } from 'react-bootstrap';

const Evaluation = () => {
  const [activeTab, setActiveTab] = useState('form');
  const [formData, setFormData] = useState({
    vendorName: '',
    contactEmail: '',
    contactPhone: '',
    financialProposal: {
      totalAmount: '',
      currency: 'INR'
    }
  });

  const handleInputChange = (field, value, section = null) => {
    if (section) {
      setFormData(prev => ({
        ...prev,
        [section]: {
          ...prev[section],
          [field]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const mockEvaluationResult = {
    vendorName: 'Sample Vendor',
    overallScore: 85.2,
    recommendation: 'RECOMMEND',
    riskLevel: 'LOW',
    complianceStatus: 'COMPLIANT',
    detailedScores: {
      financial_proposal: { score: 88, weight: 25, weighted: 22.0 },
      technical_compliance: { score: 92, weight: 20, weighted: 18.4 },
      company_profile: { score: 80, weight: 15, weighted: 12.0 },
      methodology: { score: 85, weight: 15, weighted: 12.75 },
      credentials: { score: 82, weight: 10, weighted: 8.2 },
      references: { score: 90, weight: 10, weighted: 9.0 },
      timeline: { score: 75, weight: 5, weighted: 3.75 }
    }
  };

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <h2 className="mb-1">Vendor Evaluation</h2>
          <p className="text-muted mb-0">
            Comprehensive multi-criteria evaluation of vendor proposals
          </p>
        </Col>
      </Row>

      {/* Evaluation Criteria Info */}
      <Row className="mb-4">
        <Col>
          <Alert variant="info" className="d-flex align-items-center">
            <i className="fas fa-info-circle me-2"></i>
            <div>
              <strong>Evaluation Criteria:</strong> Financial Proposal (25%), Technical Compliance (20%), 
              Company Profile (15%), Methodology (15%), Credentials (10%), References (10%), Timeline (5%)
            </div>
          </Alert>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onSelect={(k) => setActiveTab(k)}
        className="mb-4"
        variant="pills"
      >
        <Tab eventKey="form" title={
          <span><i className="fas fa-edit me-2"></i>New Evaluation</span>
        }>
          <Row>
            <Col lg={8}>
              <Card className="border-0 shadow-sm">
                <Card.Header className="bg-white">
                  <Card.Title className="h6 mb-0">Vendor Information</Card.Title>
                </Card.Header>
                <Card.Body>
                  <Form>
                    <Row>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Vendor Name *</Form.Label>
                          <Form.Control
                            type="text"
                            required
                            value={formData.vendorName}
                            onChange={(e) => handleInputChange('vendorName', e.target.value)}
                            placeholder="Company name"
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Contact Email *</Form.Label>
                          <Form.Control
                            type="email"
                            required
                            value={formData.contactEmail}
                            onChange={(e) => handleInputChange('contactEmail', e.target.value)}
                            placeholder="contact@company.com"
                          />
                        </Form.Group>
                      </Col>
                    </Row>

                    <Form.Group className="mb-3">
                      <Form.Label>Contact Phone</Form.Label>
                      <Form.Control
                        type="tel"
                        value={formData.contactPhone}
                        onChange={(e) => handleInputChange('contactPhone', e.target.value)}
                        placeholder="+91-9876543210"
                      />
                    </Form.Group>

                    <hr />
                    <h6>Financial Proposal</h6>
                    
                    <Row>
                      <Col md={8}>
                        <Form.Group className="mb-3">
                          <Form.Label>Total Amount *</Form.Label>
                          <Form.Control
                            type="number"
                            required
                            value={formData.financialProposal.totalAmount}
                            onChange={(e) => handleInputChange('totalAmount', e.target.value, 'financialProposal')}
                            placeholder="500000"
                          />
                        </Form.Group>
                      </Col>
                      <Col md={4}>
                        <Form.Group className="mb-3">
                          <Form.Label>Currency</Form.Label>
                          <Form.Select
                            value={formData.financialProposal.currency}
                            onChange={(e) => handleInputChange('currency', e.target.value, 'financialProposal')}
                          >
                            <option value="INR">INR</option>
                            <option value="USD">USD</option>
                            <option value="EUR">EUR</option>
                          </Form.Select>
                        </Form.Group>
                      </Col>
                    </Row>

                    <div className="d-flex justify-content-end mt-4">
                      <Button 
                        variant="primary" 
                        size="lg"
                        className="px-5"
                        onClick={() => setActiveTab('results')}
                      >
                        <i className="fas fa-chart-line me-2"></i>
                        Evaluate Vendor
                      </Button>
                    </div>
                  </Form>
                </Card.Body>
              </Card>
            </Col>

            <Col lg={4}>
              <Card className="border-0 shadow-sm sticky-top" style={{ top: '20px' }}>
                <Card.Header className="bg-white">
                  <Card.Title className="h6 mb-0">
                    <i className="fas fa-clipboard-list text-info me-2"></i>
                    Evaluation Criteria
                  </Card.Title>
                </Card.Header>
                <Card.Body>
                  <div className="small">
                    <div className="d-flex justify-content-between mb-2">
                      <span>Financial Proposal:</span>
                      <strong>25%</strong>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span>Technical Compliance:</span>
                      <strong>20%</strong>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span>Company Profile:</span>
                      <strong>15%</strong>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span>Methodology:</span>
                      <strong>15%</strong>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span>Credentials:</span>
                      <strong>10%</strong>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span>References:</span>
                      <strong>10%</strong>
                    </div>
                    <div className="d-flex justify-content-between">
                      <span>Timeline:</span>
                      <strong>5%</strong>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="results" title={
          <span><i className="fas fa-chart-bar me-2"></i>Results</span>
        }>
          <Row>
            <Col lg={8}>
              <Card className="border-0 shadow-sm mb-4">
                <Card.Header className="bg-white">
                  <Card.Title className="h5 mb-0">
                    Evaluation Results: {mockEvaluationResult.vendorName}
                  </Card.Title>
                </Card.Header>
                <Card.Body>
                  <Row className="text-center mb-4">
                    <Col md={3}>
                      <div className="d-flex align-items-center justify-content-center mb-2">
                        <div 
                          className="rounded-circle bg-success text-white d-flex align-items-center justify-content-center"
                          style={{ width: '80px', height: '80px', fontSize: '1.5rem', fontWeight: 'bold' }}
                        >
                          {mockEvaluationResult.overallScore}
                        </div>
                      </div>
                      <small className="text-muted">Overall Score</small>
                    </Col>
                    <Col md={3}>
                      <h3 className="text-success">{mockEvaluationResult.recommendation}</h3>
                      <small className="text-muted">Recommendation</small>
                    </Col>
                    <Col md={3}>
                      <Badge bg="info" className="p-2">
                        {mockEvaluationResult.riskLevel}
                      </Badge>
                      <br />
                      <small className="text-muted">Risk Level</small>
                    </Col>
                    <Col md={3}>
                      <Badge bg="success" className="p-2">
                        {mockEvaluationResult.complianceStatus}
                      </Badge>
                      <br />
                      <small className="text-muted">Compliance</small>
                    </Col>
                  </Row>

                  <h6>Detailed Scores</h6>
                  <Table responsive>
                    <thead>
                      <tr>
                        <th>Criteria</th>
                        <th>Score</th>
                        <th>Weight</th>
                        <th>Weighted Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(mockEvaluationResult.detailedScores).map(([key, data]) => (
                        <tr key={key}>
                          <td className="text-capitalize">{key.replace(/_/g, ' ')}</td>
                          <td>
                            <ProgressBar 
                              now={data.score} 
                              label={`${data.score}%`}
                              className="mb-0"
                              style={{ height: '20px' }}
                            />
                          </td>
                          <td>{data.weight}%</td>
                          <td className="fw-bold">{data.weighted}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
            
            <Col lg={4}>
              <Card className="border-0 shadow-sm">
                <Card.Header className="bg-white">
                  <Card.Title className="h6 mb-0">Actions</Card.Title>
                </Card.Header>
                <Card.Body>
                  <div className="d-grid gap-2">
                    <Button variant="primary">
                      <i className="fas fa-download me-2"></i>
                      Download Report
                    </Button>
                    <Button variant="outline-secondary">
                      <i className="fas fa-share me-2"></i>
                      Share Results
                    </Button>
                    <Button variant="outline-info">
                      <i className="fas fa-balance-scale me-2"></i>
                      Compare with Others
                    </Button>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
      </Tabs>
    </Container>
  );
};

export default Evaluation;
