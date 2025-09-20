"""
Enhanced Tests for Vendor Scoring
"""
import pytest
from backend.scoring.vendor_scoring import score_vendor, vendor_scorer, evaluate_vendor_comprehensive

def test_simple_scoring():
    """Test basic vendor scoring function"""
    score = score_vendor(100, 0.9, 0.8)
    assert isinstance(score, float)
    assert score > 0

def test_comprehensive_evaluation():
    """Test comprehensive vendor evaluation"""
    vendor_data = {
        'vendor_id': 'V001',
        'vendor_name': 'Test Vendor',
        'financial_proposal': {
            'total_amount': 500000,
            'payment_terms': 'Net 30'
        },
        'technical_proposal': {
            'specifications': {'software': 'Python', 'database': 'PostgreSQL'}
        },
        'company_profile': {
            'years_in_business': 10,
            'annual_turnover': 10000000,
            'certifications': ['ISO 9001']
        },
        'methodology': {
            'approach': 'Agile development methodology with iterative delivery and continuous integration.',
            'phases': ['Analysis', 'Design', 'Development', 'Testing', 'Deployment']
        },
        'credentials': {
            'team_members': [
                {'role': 'Project Manager', 'experience_years': 8, 'education': 'MBA'},
                {'role': 'Lead Developer', 'experience_years': 6, 'education': 'B.Tech Computer Science'}
            ]
        },
        'references': [
            {
                'client_name': 'Government Agency',
                'client_type': 'government',
                'project_value': 400000,
                'completion_date': '2023-06-15',
                'performance_rating': 4.5
            }
        ],
        'timeline': {
            'duration_days': 120,
            'milestones': ['Requirement Analysis', 'Design', 'Development', 'Testing', 'Deployment']
        }
    }
    
    tender_requirements = {
        'estimated_value': 600000,
        'budget_range_min': 400000,
        'budget_range_max': 700000,
        'max_duration_days': 150,
        'technical_requirements': {
            'mandatory': [
                {'key': 'software', 'value': 'Python'}
            ]
        },
        'min_annual_turnover': 5000000,
        'required_roles': ['Project Manager', 'Lead Developer']
    }
    
    evaluation_result = evaluate_vendor_comprehensive(vendor_data, tender_requirements)
    
    assert isinstance(evaluation_result, dict)
    assert 'vendor_name' in evaluation_result
    assert 'overall_score' in evaluation_result
    assert 'weighted_score' in evaluation_result
    assert 'recommendation' in evaluation_result
    assert 'criteria_scores' in evaluation_result

def test_vendor_comparison():
    """Test vendor comparison functionality"""
    # Create sample evaluations
    evaluations = [
        {
            'vendor_id': 'V001',
            'vendor_name': 'Vendor A',
            'overall_score': 85.0,
            'weighted_score': 82.0,
            'recommendation': 'RECOMMEND',
            'risk_level': 'low',
            'compliance_status': 'compliant',
            'criteria_scores': {},
            'evaluation_timestamp': '2024-01-01T00:00:00'
        },
        {
            'vendor_id': 'V002', 
            'vendor_name': 'Vendor B',
            'overall_score': 75.0,
            'weighted_score': 73.0,
            'recommendation': 'CONDITIONALLY RECOMMEND',
            'risk_level': 'medium',
            'compliance_status': 'partial',
            'criteria_scores': {},
            'evaluation_timestamp': '2024-01-01T00:00:00'
        }
    ]
    
    try:
        from backend.scoring.vendor_scoring import compare_vendors_detailed
        comparison = compare_vendors_detailed(evaluations)
        
        assert isinstance(comparison, dict)
        assert 'ranking' in comparison
        assert 'statistics' in comparison
    except ImportError:
        pytest.skip("Vendor comparison function not available")

def test_risk_assessment():
    """Test risk assessment functionality"""
    # Test with high-risk vendor data
    high_risk_vendor = {
        'vendor_id': 'V003',
        'vendor_name': 'High Risk Vendor',
        'financial_proposal': {
            'total_amount': 50000  # Very low amount
        },
        'company_profile': {
            'years_in_business': 1,  # New company
            'annual_turnover': 100000  # Low turnover
        },
        'credentials': {
            'team_members': []  # No team info
        },
        'references': []  # No references
    }
    
    tender_requirements = {
        'estimated_value': 500000,
        'budget_range_min': 400000,
        'budget_range_max': 600000,
        'min_annual_turnover': 1000000
    }
    
    evaluation = evaluate_vendor_comprehensive(high_risk_vendor, tender_requirements)
    
    # Should have low scores and high risk
    assert evaluation['overall_score'] < 60
    assert 'NOT' in evaluation['recommendation'] or 'REJECT' in evaluation['recommendation']
