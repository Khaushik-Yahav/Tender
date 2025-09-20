import React from 'react';
import { Nav } from 'react-bootstrap';
import { useLocation, Link } from 'react-router-dom';

const Sidebar = () => {
  const location = useLocation();

  const menuItems = [
    {
      path: '/dashboard',
      icon: 'fas fa-tachometer-alt',
      label: 'Dashboard',
      description: 'Overview & Statistics'
    },
    {
      path: '/documents',
      icon: 'fas fa-file-alt',
      label: 'Documents',
      description: 'Upload & Manage'
    },
    {
      path: '/evaluation',
      icon: 'fas fa-chart-line',
      label: 'Evaluation',
      description: 'Vendor Assessment'
    },
    {
      path: '/chat',
      icon: 'fas fa-comments',
      label: 'AI Assistant',
      description: 'Ask Questions'
    },
    {
      path: '/reports',
      icon: 'fas fa-file-pdf',
      label: 'Reports',
      description: 'Generate Reports'
    }
  ];

  return (
    <div className="sidebar bg-light border-end h-100">
      <div className="sidebar-header p-3 border-bottom">
        <h6 className="text-muted mb-0">Navigation</h6>
      </div>
      
      <Nav className="flex-column p-2">
        {menuItems.map((item) => (
          <Nav.Item key={item.path} className="mb-1">
            <Nav.Link
              as={Link}
              to={item.path}
              className={`sidebar-link rounded ${
                location.pathname === item.path ? 'active' : ''
              }`}
            >
              <div className="d-flex align-items-center">
                <i className={`${item.icon} me-3`}></i>
                <div>
                  <div className="fw-medium">{item.label}</div>
                  <small className="text-muted">{item.description}</small>
                </div>
              </div>
            </Nav.Link>
          </Nav.Item>
        ))}
      </Nav>
    </div>
  );
};

export default Sidebar;
