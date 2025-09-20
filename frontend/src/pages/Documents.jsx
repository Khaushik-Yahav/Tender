import React, { useState } from 'react';
import { Container, Row, Col, Card, Tab, Tabs, Table, Button, Badge, Form, InputGroup } from 'react-bootstrap';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';

const Documents = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    tenderId: '',
    documentType: 'general',
    description: ''
  });

  // Mock document data (replace with real API call)
  const mockDocuments = [
    { id: 1, name: 'Software Development RFP.pdf', type: 'Tender Document', size: '2.3 MB', date: '2024-12-15', status: 'Processed' },
    { id: 2, name: 'TechCorp Proposal.docx', type: 'Vendor Proposal', size: '1.8 MB', date: '2024-12-14', status: 'Processing' },
    { id: 3, name: 'Technical Specifications.pdf', type: 'Technical Spec', size: '3.1 MB', date: '2024-12-13', status: 'Processed' }
  ];

  const uploadMutation = useMutation({
    mutationFn: apiService.uploadDocument,
    onSuccess: () => {
      toast.success('Document uploaded successfully!');
      setUploadProgress(0);
    },
    onError: () => {
      toast.error('Failed to upload document');
      setUploadProgress(0);
    }
  });

  const onDrop = (acceptedFiles) => {
    acceptedFiles.forEach((file) => {
      const formDataToSend = new FormData();
      formDataToSend.append('file', file);
      formDataToSend.append('tender_id', formData.tenderId || 'general');
      formDataToSend.append('document_type', formData.documentType);
      formDataToSend.append('description', formData.description);

      // Simulate upload progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setUploadProgress(progress);
        if (progress >= 90) {
          clearInterval(interval);
        }
      }, 200);

      uploadMutation.mutate(formDataToSend);
    });
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png']
    },
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  const documentTypes = [
    { value: 'tender_document', label: 'Tender Document' },
    { value: 'vendor_proposal', label: 'Vendor Proposal' },
    { value: 'technical_specification', label: 'Technical Specification' },
    { value: 'financial_proposal', label: 'Financial Proposal' },
    { value: 'compliance_document', label: 'Compliance Document' },
    { value: 'general', label: 'General Document' }
  ];

  const filteredDocuments = mockDocuments.filter(doc =>
    doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <h2 className="mb-1">Document Management</h2>
          <p className="text-muted mb-0">
            Upload, process, and manage tender documents and vendor proposals
          </p>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onSelect={(k) => setActiveTab(k)}
        className="mb-4"
        variant="pills"
      >
        <Tab eventKey="upload" title={
          <span><i className="fas fa-cloud-upload-alt me-2"></i>Upload Documents</span>
        }>
          <Row>
            <Col lg={8}>
              <Card className="border-0 shadow-sm mb-4">
                <Card.Header className="bg-white">
                  <Card.Title className="h6 mb-0">
                    <i className="fas fa-cloud-upload-alt text-primary me-2"></i>
                    Upload Documents
                  </Card.Title>
                </Card.Header>
                <Card.Body>
                  <Form className="mb-4">
                    <Row>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Tender ID (Optional)</Form.Label>
                          <Form.Control
                            type="text"
                            placeholder="e.g., TND-2024-001"
                            value={formData.tenderId}
                            onChange={(e) => setFormData(prev => ({ ...prev, tenderId: e.target.value }))}
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Document Type</Form.Label>
                          <Form.Select
                            value={formData.documentType}
                            onChange={(e) => setFormData(prev => ({ ...prev, documentType: e.target.value }))}
                          >
                            {documentTypes.map(type => (
                              <option key={type.value} value={type.value}>
                                {type.label}
                              </option>
                            ))}
                          </Form.Select>
                        </Form.Group>
                      </Col>
                    </Row>
                    <Form.Group className="mb-3">
                      <Form.Label>Description (Optional)</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={2}
                        placeholder="Brief description of the document..."
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                      />
                    </Form.Group>
                  </Form>

                  <div 
                    {...getRootProps()} 
                    className={`upload-zone ${isDragActive ? 'dragover' : ''}`}
                  >
                    <input {...getInputProps()} />
                    <div className="text-center">
                      <i className={`fas fa-cloud-upload-alt fa-3x mb-3 ${isDragActive ? 'text-success' : 'text-muted'}`}></i>
                      <h5>{isDragActive ? 'Drop files here' : 'Drag & drop files here'}</h5>
                      <p className="text-muted mb-3">
                        or <Button variant="outline-primary" size="sm">browse files</Button>
                      </p>
                      <small className="text-muted">
                        Supported formats: PDF, DOCX, TXT, JPG, PNG (Max 50MB each)
                      </small>
                    </div>
                  </div>

                  {uploadProgress > 0 && (
                    <div className="mt-3">
                      <div className="d-flex justify-content-between align-items-center mb-2">
                        <small className="text-muted">Uploading...</small>
                        <small className="text-muted">{uploadProgress}%</small>
                      </div>
                      <div className="progress">
                        <div 
                          className="progress-bar" 
                          role="progressbar" 
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>

            <Col lg={4}>
              <Card className="border-0 shadow-sm mb-3">
                <Card.Header className="bg-white">
                  <Card.Title className="h6 mb-0">
                    <i className="fas fa-info-circle text-info me-2"></i>
                    Upload Guidelines
                  </Card.Title>
                </Card.Header>
                <Card.Body>
                  <ul className="list-unstyled mb-0 small">
                    <li className="mb-2">
                      <i className="fas fa-check text-success me-2"></i>
                      Files are automatically processed with AI
                    </li>
                    <li className="mb-2">
                      <i className="fas fa-check text-success me-2"></i>
                      Text is extracted and indexed for search
                    </li>
                    <li className="mb-2">
                      <i className="fas fa-check text-success me-2"></i>
                      OCR is applied to scanned documents
                    </li>
                    <li>
                      <i className="fas fa-check text-success me-2"></i>
                      Documents are ready for Q&A immediately
                    </li>
                  </ul>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="list" title={
          <span><i className="fas fa-list me-2"></i>Document Library</span>
        }>
          <Row className="mb-3">
            <Col md={6}>
              <InputGroup>
                <InputGroup.Text>
                  <i className="fas fa-search"></i>
                </InputGroup.Text>
                <Form.Control
                  placeholder="Search documents..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </InputGroup>
            </Col>
            <Col md={6} className="text-end">
              <Button variant="outline-secondary" size="sm" className="me-2">
                <i className="fas fa-filter me-1"></i>Filter
              </Button>
              <Button variant="primary" size="sm">
                <i className="fas fa-sync me-1"></i>Refresh
              </Button>
            </Col>
          </Row>

          <Card className="border-0 shadow-sm">
            <Card.Body className="p-0">
              <Table responsive hover className="mb-0">
                <thead className="bg-light">
                  <tr>
                    <th>Document Name</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDocuments.map(doc => (
                    <tr key={doc.id}>
                      <td className="fw-medium">
                        <i className="fas fa-file-alt text-primary me-2"></i>
                        {doc.name}
                      </td>
                      <td>{doc.type}</td>
                      <td>{doc.size}</td>
                      <td>{doc.date}</td>
                      <td>
                        <Badge bg={doc.status === 'Processed' ? 'success' : 'warning'}>
                          {doc.status}
                        </Badge>
                      </td>
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
        </Tab>
      </Tabs>
    </Container>
  );
};

export default Documents;
