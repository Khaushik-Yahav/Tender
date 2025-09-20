import React from 'react';
import { Container } from 'react-bootstrap';

const Footer = () => {
  return (
    <footer className="bg-light border-top mt-auto py-3">
      <Container fluid>
        <div className="row align-items-center">
          <div className="col-md-6">
            <small className="text-muted">
              © 2024 Tender Evaluation System. Powered by AI.
            </small>
          </div>
          <div className="col-md-6 text-md-end">
            <small className="text-muted">
              Version 2.0.0 | 
              <a href="/docs" className="text-decoration-none ms-1" target="_blank" rel="noopener noreferrer">
                API Documentation
              </a>
            </small>
          </div>
        </div>
      </Container>
    </footer>
  );
};

export default Footer;
