import React, { useState, useEffect } from 'react';
import { Card, Table, Badge, ProgressBar, Alert, Spinner, Button, Row, Col, Tabs, Tab } from 'react-bootstrap';
import { FaCheckCircle, FaTimesCircle, FaExclamationTriangle } from 'react-icons/fa';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function ComplianceReport({ tender, companyName, onBack }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReport();
  }, [tender, companyName]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/tenders/${tender.tender_id}/companies/${companyName}/report`
      );
      setReport(response.data.compliance_report);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error fetching report');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p>Loading compliance report...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        <h5>Error</h5>
        <p>{error}</p>
        <Button variant="secondary" onClick={onBack}>← Back</Button>
      </Alert>
    );
  }

  if (!report) {
    return null;
  }

  const getStatusIcon = (status) => {
    if (status === 'met') return <FaCheckCircle className="text-success" />;
    if (status === 'partial') return <FaExclamationTriangle className="text-warning" />;
    return <FaTimesCircle className="text-danger" />;
  };

  const getStatusBadge = (status) => {
    if (status === 'met') return <Badge bg="success">Met</Badge>;
    if (status === 'partial') return <Badge bg="warning">Partial</Badge>;
    return <Badge bg="danger">Missing</Badge>;
  };

  const getComplianceColor = (percentage) => {
    if (percentage >= 80) return 'success';
    if (percentage >= 60) return 'warning';
    return 'danger';
  };

  return (
    <>
      <Card className="mb-3">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h4>📊 Compliance Report - {companyName}</h4>
          <Button variant="secondary" size="sm" onClick={onBack}>
            ← Back to List
          </Button>
        </Card.Header>
      </Card>

      {/* Summary Cards */}
      <Row className="mb-3">
        <Col md={3}>
          <Card className="text-center summary-card-success">
            <Card.Body>
              <h2>{report.compliance_percentage}%</h2>
              <p className="mb-0">Overall Compliance</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center summary-card-info">
            <Card.Body>
              <h2>{report.requirements_met.length}</h2>
              <p className="mb-0">Requirements Met</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center summary-card-warning">
            <Card.Body>
              <h2>{report.requirements_partial.length}</h2>
              <p className="mb-0">Partially Met</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center summary-card-danger">
            <Card.Body>
              <h2>{report.requirements_missing.length}</h2>
              <p className="mb-0">Missing</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Progress Bar */}
      <Card className="mb-3">
        <Card.Body>
          <h6>Compliance Progress</h6>
          <ProgressBar>
            <ProgressBar
              variant="success"
              now={(report.requirements_met.length / report.total_requirements) * 100}
              label={`${report.requirements_met.length} Met`}
            />
            <ProgressBar
              variant="warning"
              now={(report.requirements_partial.length / report.total_requirements) * 100}
              label={`${report.requirements_partial.length} Partial`}
            />
            <ProgressBar
              variant="danger"
              now={(report.requirements_missing.length / report.total_requirements) * 100}
              label={`${report.requirements_missing.length} Missing`}
            />
          </ProgressBar>
        </Card.Body>
      </Card>

      {/* Detailed Requirements */}
      <Card>
        <Card.Header>
          <h5>Detailed Requirements Analysis</h5>
        </Card.Header>
        <Card.Body>
          <Tabs defaultActiveKey="all" className="mb-3">
            <Tab eventKey="all" title={`All (${report.detailed_results.length})`}>
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th style={{width: '80px'}}>Status</th>
                    <th style={{width: '100px'}}>Req ID</th>
                    <th>Requirement</th>
                    <th style={{width: '120px'}}>Confidence</th>
                    <th style={{width: '200px'}}>Reasoning</th>
                  </tr>
                </thead>
                <tbody>
                  {report.detailed_results.map((result) => (
                    <tr key={result.req_id}>
                      <td className="text-center">
                        {getStatusIcon(result.status)}
                        <br />
                        {getStatusBadge(result.status)}
                      </td>
                      <td><code>{result.req_id}</code></td>
                      <td>{result.requirement_text}</td>
                      <td>
                        <ProgressBar
                          now={result.confidence_score * 100}
                          label={`${(result.confidence_score * 100).toFixed(0)}%`}
                          variant={result.confidence_score >= 0.7 ? 'success' : result.confidence_score >= 0.5 ? 'warning' : 'danger'}
                        />
                      </td>
                      <td><small>{result.reasoning}</small></td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Tab>

            <Tab eventKey="met" title={`Met (${report.requirements_met.length})`}>
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th>Req ID</th>
                    <th>Requirement</th>
                    <th>Confidence</th>
                    <th>Matched Sections</th>
                  </tr>
                </thead>
                <tbody>
                  {report.detailed_results
                    .filter(r => r.status === 'met')
                    .map((result) => (
                      <tr key={result.req_id}>
                        <td><code>{result.req_id}</code></td>
                        <td>{result.requirement_text}</td>
                        <td>
                          <Badge bg="success">
                            {(result.confidence_score * 100).toFixed(0)}%
                          </Badge>
                        </td>
                        <td>
                          {result.matched_sections.slice(0, 2).map((section, idx) => (
                            <div key={idx} className="mb-2">
                              <small className="text-muted">{section}</small>
                            </div>
                          ))}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </Table>
            </Tab>

            <Tab eventKey="partial" title={`Partial (${report.requirements_partial.length})`}>
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th>Req ID</th>
                    <th>Requirement</th>
                    <th>Confidence</th>
                    <th>Reasoning</th>
                  </tr>
                </thead>
                <tbody>
                  {report.detailed_results
                    .filter(r => r.status === 'partial')
                    .map((result) => (
                      <tr key={result.req_id}>
                        <td><code>{result.req_id}</code></td>
                        <td>{result.requirement_text}</td>
                        <td>
                          <Badge bg="warning">
                            {(result.confidence_score * 100).toFixed(0)}%
                          </Badge>
                        </td>
                        <td><small>{result.reasoning}</small></td>
                      </tr>
                    ))}
                </tbody>
              </Table>
            </Tab>

            <Tab eventKey="missing" title={`Missing (${report.requirements_missing.length})`}>
              <Alert variant="danger">
                <strong>⚠️ Missing Requirements</strong>
                <p>The following requirements were not found in the submitted documents:</p>
              </Alert>
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th>Req ID</th>
                    <th>Requirement</th>
                    <th>Reasoning</th>
                  </tr>
                </thead>
                <tbody>
                  {report.detailed_results
                    .filter(r => r.status === 'missing')
                    .map((result) => (
                      <tr key={result.req_id}>
                        <td><code>{result.req_id}</code></td>
                        <td>{result.requirement_text}</td>
                        <td><small className="text-danger">{result.reasoning}</small></td>
                      </tr>
                    ))}
                </tbody>
              </Table>
            </Tab>
          </Tabs>
        </Card.Body>
      </Card>
    </>
  );
}

export default ComplianceReport;
