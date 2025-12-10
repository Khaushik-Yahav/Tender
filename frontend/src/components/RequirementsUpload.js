import React, { useState, useEffect } from 'react';
import { Card, Form, Button, Alert, Table, Badge, Spinner } from 'react-bootstrap';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function RequirementsUpload({ tender, onSuccess, onBack }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [requirements, setRequirements] = useState([]);
  const [loadingRequirements, setLoadingRequirements] = useState(false);

  useEffect(() => {
    if (tender.requirements_document) {
      fetchRequirements();
    }
  }, [tender]);

  const fetchRequirements = async () => {
    setLoadingRequirements(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/tenders/${tender.tender_id}/requirements`);
      setRequirements(response.data.requirements || []);
    } catch (err) {
      console.error('Error fetching requirements:', err);
    } finally {
      setLoadingRequirements(false);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const handleUpload = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/tenders/${tender.tender_id}/requirements`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      setSuccess(`Successfully extracted ${response.data.total_requirements} requirements!`);
      setRequirements(response.data.requirements || []);
      setFile(null);
      document.getElementById('requirementsFile').value = '';
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading requirements');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryBadge = (category) => {
    const colors = {
      'Technical': 'primary',
      'Financial': 'success',
      'Compliance': 'warning',
      'Timeline': 'info',
      'Eligibility': 'secondary',
      'General': 'dark'
    };
    return colors[category] || 'secondary';
  };

  return (
    <>
      <Card className="mb-3">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h4>📄 Requirements Upload - {tender.tender_name}</h4>
          <Button variant="secondary" size="sm" onClick={onBack}>
            ← Back to List
          </Button>
        </Card.Header>
        <Card.Body>
          <Alert variant="info">
            <strong>Upload Government Requirements Document</strong>
            <p className="mb-0">
              Upload the official tender requirements document (PDF, DOCX, TXT). 
              The system will automatically extract all requirements.
            </p>
          </Alert>

          {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
          {success && <Alert variant="success" dismissible onClose={() => setSuccess('')}>{success}</Alert>}

          <Form onSubmit={handleUpload}>
            <Form.Group className="mb-3">
              <Form.Label>Requirements Document</Form.Label>
              <Form.Control
                id="requirementsFile"
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
              />
              <Form.Text className="text-muted">
                Accepted formats: PDF, DOCX, TXT
              </Form.Text>
            </Form.Group>

            <Button variant="primary" type="submit" disabled={loading || !file}>
              {loading ? (
                <>
                  <Spinner animation="border" size="sm" /> Uploading & Extracting...
                </>
              ) : (
                'Upload & Extract Requirements'
              )}
            </Button>
          </Form>
        </Card.Body>
      </Card>

      {/* Display Extracted Requirements */}
      {requirements.length > 0 && (
        <Card>
          <Card.Header>
            <h5>📋 Extracted Requirements ({requirements.length})</h5>
          </Card.Header>
          <Card.Body>
            {loadingRequirements ? (
              <div className="text-center py-5">
                <Spinner animation="border" />
                <p>Loading requirements...</p>
              </div>
            ) : (
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th style={{width: '100px'}}>Req ID</th>
                    <th>Requirement Text</th>
                    <th style={{width: '120px'}}>Category</th>
                    <th style={{width: '100px'}}>Mandatory</th>
                  </tr>
                </thead>
                <tbody>
                  {requirements.map((req) => (
                    <tr key={req.req_id}>
                      <td><code>{req.req_id}</code></td>
                      <td>{req.requirement_text}</td>
                      <td>
                        <Badge bg={getCategoryBadge(req.category)}>
                          {req.category}
                        </Badge>
                      </td>
                      <td>
                        {req.mandatory ? (
                          <Badge bg="danger">Yes</Badge>
                        ) : (
                          <Badge bg="secondary">No</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Card.Body>
        </Card>
      )}
    </>
  );
}

export default RequirementsUpload;
