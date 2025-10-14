import React, { useState, useEffect } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import { Container, Row, Col, Card, Table, ProgressBar, Button, Spinner, Modal } from "react-bootstrap";
import { Bar } from "react-chartjs-2";
import { FaFileUpload, FaChartBar, FaList, FaEye } from "react-icons/fa";
import "./App.css";

// Chart.js v3+ registration
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function App() {
  const [file, setFile] = useState(null);
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [latestTender, setLatestTender] = useState(null);
  const [activeView, setActiveView] = useState("upload"); // upload, dashboard, history
  const [showModal, setShowModal] = useState(false);
  const [modalTender, setModalTender] = useState(null);

  useEffect(() => {
    fetchTenders();
  }, []);

  const fetchTenders = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:8000/tenders");
      setTenders(response.data);
      if (response.data.length > 0) {
        setLatestTender(response.data[response.data.length - 1]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return alert("Please select a file first");

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/analyze/file",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setLatestTender(response.data);
      fetchTenders();
      setActiveView("dashboard"); // Switch to dashboard after upload
    } catch (err) {
      console.error(err);
      alert("Error analyzing the tender file.");
    } finally {
      setLoading(false);
    }
  };

  const openModal = (tender) => {
    setModalTender(tender);
    setShowModal(true);
  };

  const closeModal = () => setShowModal(false);

  // Chart Data
  const chartData = {
    labels: tenders.map(t => t.filename),
    datasets: [
      {
        label: "Tender Scores",
        data: tenders.map(t => t.final_score),
        backgroundColor: "rgba(102, 205, 170, 0.7)",
        borderColor: "rgba(102, 205, 170, 1)",
        borderWidth: 1
      }
    ]
  };

  return (
    <div className="dashboard">
      {/* Sidebar */}
      <aside className="sidebar">
        <h2>Tender Analyzer</h2>
        <nav>
          <ul>
            <li
              className={activeView === "upload" ? "active" : ""}
              onClick={() => setActiveView("upload")}
            >
              <FaFileUpload /> Upload
            </li>
            <li
              className={activeView === "dashboard" ? "active" : ""}
              onClick={() => setActiveView("dashboard")}
            >
              <FaChartBar /> Dashboard
            </li>
            <li
              className={activeView === "history" ? "active" : ""}
              onClick={() => setActiveView("history")}
            >
              <FaList /> History
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Container>
          {/* Upload View */}
          {activeView === "upload" && (
            <Row className="mb-4">
              <Col md={6}>
                <Card>
                  <Card.Body>
                    <Card.Title>Upload Tender</Card.Title>
                    <form onSubmit={handleSubmit} className="upload-form">
                      <input type="file" onChange={handleFileChange} />
                      <Button variant="primary" type="submit" disabled={loading}>
                        {loading ? <Spinner animation="border" size="sm" /> : "Analyze"}
                      </Button>
                    </form>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          )}

          {/* Dashboard View */}
          {activeView === "dashboard" && (
            <>
              <Row className="mb-4">
                <Col md={4}>
                  <Card className="summary-card">
                    <Card.Body>
                      <Card.Title>Total Tenders</Card.Title>
                      <Card.Text>{tenders.length}</Card.Text>
                    </Card.Body>
                  </Card>
                </Col>
                <Col md={4}>
                  <Card className="summary-card">
                    <Card.Body>
                      <Card.Title>Highest Score</Card.Title>
                      <Card.Text>
                        {tenders.length > 0 ? Math.max(...tenders.map(t => t.final_score)) : 0}
                      </Card.Text>
                    </Card.Body>
                  </Card>
                </Col>
                <Col md={4}>
                  <Card className="summary-card">
                    <Card.Body>
                      <Card.Title>Latest Tender</Card.Title>
                      <Card.Text>{latestTender ? latestTender.filename : "N/A"}</Card.Text>
                      {latestTender && (
                        <ProgressBar now={latestTender.final_score} label={`${latestTender.final_score}`} />
                      )}
                    </Card.Body>
                  </Card>
                </Col>
              </Row>

              <Row className="mb-4">
                <Col>
                  <Card>
                    <Card.Body>
                      <Card.Title>Score Chart</Card.Title>
                      <Bar key={tenders.length} data={chartData} />
                    </Card.Body>
                  </Card>
                </Col>
              </Row>
            </>
          )}

          {/* History View */}
          {activeView === "history" && (
            <Row>
              <Col>
                <Card>
                  <Card.Body>
                    <Card.Title>Tender History</Card.Title>
                    <Table striped bordered hover responsive>
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Filename</th>
                          <th>Score</th>
                          <th>Rank</th>
                          <th>Percentile</th>
                          <th>Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tenders.map((t, idx) => (
                          <tr key={idx}>
                            <td>{idx + 1}</td>
                            <td>{t.filename}</td>
                            <td>{t.final_score}</td>
                            <td>{t.rank}</td>
                            <td>{t.percentile?.toFixed(1)}%</td>
                            <td>
                              <Button size="sm" onClick={() => openModal(t)}>
                                <FaEye /> View
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          )}
        </Container>

        {/* Modal for Detailed Scoring */}
        <Modal show={showModal} onHide={closeModal}>
          <Modal.Header closeButton>
            <Modal.Title>Detailed Scores - {modalTender?.filename}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {modalTender && (
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th>Feature</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(modalTender.features).map(([key, value]) => (
                    <tr key={key}>
                      <td>{key}</td>
                      <td>{typeof value === "number" ? value.toFixed(3) : value}</td>
                    </tr>
                  ))}
                  <tr>
                    <td><strong>Final Score</strong></td>
                    <td><strong>{modalTender.final_score}</strong></td>
                  </tr>
                </tbody>
              </Table>
            )}
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={closeModal}>Close</Button>
          </Modal.Footer>
        </Modal>
      </main>
    </div>
  );
}

export default App;
