"""
Enhanced Vendor Scoring System for Tender Evaluation
Comprehensive multi-criteria evaluation framework with AI-powered insights
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from backend.config import EVALUATION_WEIGHTS, RISK_THRESHOLDS

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    UNCLEAR = "unclear"

@dataclass
class CriteriaScore:
    raw_score: float
    weighted_score: float
    confidence: float
    justification: str
    risk_flags: List[str]

@dataclass
class VendorEvaluation:
    vendor_id: str
    vendor_name: str
    criteria_scores: Dict[str, CriteriaScore]
    overall_score: float
    weighted_score: float
    risk_level: RiskLevel
    compliance_status: ComplianceStatus
    recommendation: str
    evaluation_timestamp: str
    evaluator_notes: str = ""

class AdvancedVendorScorer:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or EVALUATION_WEIGHTS
        self.risk_thresholds = RISK_THRESHOLDS
        
        # Ensure weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, normalizing...")
            self.weights = {k: v/total_weight for k, v in self.weights.items()}
    
    def evaluate_vendor_comprehensive(self, vendor_data: Dict[str, Any], 
                                    tender_requirements: Dict[str, Any],
                                    context_data: Optional[Dict[str, Any]] = None) -> VendorEvaluation:
        """
        Comprehensive vendor evaluation with detailed scoring
        """
        try:
            vendor_id = vendor_data.get('vendor_id', 'unknown')
            vendor_name = vendor_data.get('vendor_name', 'Unknown Vendor')
            
            logger.info(f"Evaluating vendor: {vendor_name}")
            
            # Evaluate each criterion
            criteria_scores = {}
            
            # Financial Proposal Evaluation
            criteria_scores['financial_proposal'] = self._evaluate_financial_proposal(
                vendor_data, tender_requirements, context_data
            )
            
            # Technical Compliance Evaluation
            criteria_scores['technical_compliance'] = self._evaluate_technical_compliance(
                vendor_data, tender_requirements, context_data
            )
            
            # Company Profile Evaluation
            criteria_scores['company_profile'] = self._evaluate_company_profile(
                vendor_data, tender_requirements, context_data
            )
            
            # Methodology Evaluation
            criteria_scores['methodology'] = self._evaluate_methodology(
                vendor_data, tender_requirements, context_data
            )
            
            # Credentials Evaluation
            criteria_scores['credentials'] = self._evaluate_credentials(
                vendor_data, tender_requirements, context_data
            )
            
            # References Evaluation
            criteria_scores['references'] = self._evaluate_references(
                vendor_data, tender_requirements, context_data
            )
            
            # Timeline Evaluation
            criteria_scores['timeline'] = self._evaluate_timeline(
                vendor_data, tender_requirements, context_data
            )
            
            # Calculate overall scores
            overall_score = np.mean([score.raw_score for score in criteria_scores.values()])
            weighted_score = sum(score.weighted_score for score in criteria_scores.values())
            
            # Assess overall risk
            risk_level = self._assess_overall_risk(criteria_scores, vendor_data)
            
            # Determine compliance status
            compliance_status = self._determine_compliance_status(criteria_scores)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                overall_score, weighted_score, risk_level, compliance_status
            )
            
            evaluation = VendorEvaluation(
                vendor_id=vendor_id,
                vendor_name=vendor_name,
                criteria_scores=criteria_scores,
                overall_score=overall_score,
                weighted_score=weighted_score,
                risk_level=risk_level,
                compliance_status=compliance_status,
                recommendation=recommendation,
                evaluation_timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"Evaluation complete for {vendor_name}: {weighted_score:.2f}/100")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating vendor: {e}")
            # Return default evaluation on error
            return self._create_error_evaluation(vendor_data, str(e))
    
    def _evaluate_financial_proposal(self, vendor_data: Dict[str, Any], 
                                   tender_requirements: Dict[str, Any],
                                   context_data: Optional[Dict[str, Any]]) -> CriteriaScore:
        """Evaluate financial proposal"""
        
        proposed_amount = vendor_data.get('financial_proposal', {}).get('total_amount', 0)
        estimated_value = tender_requirements.get('estimated_value', 0)
        budget_min = tender_requirements.get('budget_range_min', 0)
        budget_max = tender_requirements.get('budget_range_max', float('inf'))
        
        raw_score = 50.0  # Base score
        risk_flags = []
        justification_parts = []
        
        if proposed_amount <= 0:
            raw_score = 0
            risk_flags.append("No financial proposal provided")
            justification_parts.append("Missing financial proposal")
        else:
            # Budget compliance check
            if budget_min <= proposed_amount <= budget_max:
                raw_score += 30
                justification_parts.append(f"Amount within budget range: ₹{proposed_amount:,.0f}")
            elif proposed_amount > budget_max:
                excess_percentage = (proposed_amount - budget_max) / budget_max * 100
                raw_score -= min(30, excess_percentage)
                risk_flags.append(f"Exceeds budget by {excess_percentage:.1f}%")
                justification_parts.append(f"Amount exceeds budget range")
            else:
                # Below minimum - could be aggressive pricing
                discount_percentage = (budget_min - proposed_amount) / budget_min * 100
                if discount_percentage > 30:
                    risk_flags.append(f"Unusually low bid ({discount_percentage:.1f}% below minimum)")
                    raw_score -= 10
                else:
                    raw_score += 20  # Competitive pricing
                justification_parts.append(f"Competitive pricing: {discount_percentage:.1f}% below minimum")
            
            # Value for money assessment
            if estimated_value > 0:
                value_ratio = proposed_amount / estimated_value
                if 0.8 <= value_ratio <= 1.2:
                    raw_score += 15
                    justification_parts.append("Good value proposition")
                elif value_ratio < 0.5:
                    risk_flags.append("Unrealistically low pricing")
                    raw_score -= 20
                elif value_ratio > 2.0:
                    risk_flags.append("Significantly overpriced")
                    raw_score -= 15
            
            # Payment terms evaluation
            payment_terms = vendor_data.get('financial_proposal', {}).get('payment_terms', '')
            if 'advance' in payment_terms.lower():
                if 'advance payment' in tender_requirements.get('payment_terms', '').lower():
                    raw_score += 5
                else:
                    risk_flags.append("Requesting advance payment")
                    raw_score -= 10
        
        raw_score = max(0, min(100, raw_score))
        weighted_score = raw_score * self.weights['financial_proposal']
        
        return CriteriaScore(
            raw_score=raw_score,
            weighted_score=weighted_score,
            confidence=0.9,  # High confidence for numerical data
            justification=" | ".join(justification_parts) or "Financial evaluation completed",
            risk_flags=risk_flags
        )
    
    def _evaluate_technical_compliance(self, vendor_data: Dict[str, Any], 
                                     tender_requirements: Dict[str, Any],
                                     context_data: Optional[Dict[str, Any]]) -> CriteriaScore:
        """Evaluate technical compliance"""
        
        technical_proposal = vendor_data.get('technical_proposal', {})
        requirements = tender_requirements.get('technical_requirements', {})
        
        raw_score = 40.0  # Base score
        risk_flags = []
        justification_parts = []
        
        # Check mandatory technical requirements
        mandatory_requirements = requirements.get('mandatory', [])
        compliance_count = 0
        
        for req in mandatory_requirements:
            req_key = req.get('key', '')
            if req_key in technical_proposal:
                proposed_value = technical_proposal[req_key]
                required_value = req.get('value', '')
                
                if str(proposed_value).lower() == str(required_value).lower():
                    compliance_count += 1
                else:
                    risk_flags.append(f"Non-compliance: {req_key}")
        
        if mandatory_requirements:
            compliance_ratio = compliance_count / len(mandatory_requirements)
            raw_score += compliance_ratio * 40
            justification_parts.append(f"Mandatory compliance: {compliance_ratio:.1%}")
        else:
            raw_score += 20  # No specific requirements to check
        
        # Evaluate technical specifications
        specifications = technical_proposal.get('specifications', {})
        if specifications:
            raw_score += 10
            justification_parts.append("Technical specifications provided")
        else:
            risk_flags.append("Missing technical specifications")
        
        # Check for additional features/value-adds
        additional_features = technical_proposal.get('additional_features', [])
        if additional_features:
            raw_score += min(10, len(additional_features) * 2)
            justification_parts.append(f"Additional features: {len(additional_features)}")
        
        raw_score = max(0, min(100, raw_score))
        weighted_score = raw_score * self.weights['technical_compliance']
        
        return CriteriaScore(
            raw_score=raw_score,
            weighted_score=weighted_score,
            confidence=0.8,
            justification=" | ".join(justification_parts) or "Technical evaluation completed",
            risk_flags=risk_flags
        )
    
    def _evaluate_company_profile(self, vendor_data: Dict[str, Any], 
                                tender_requirements: Dict[str, Any],
                                context_data: Optional[Dict[str, Any]]) -> CriteriaScore:
        """Evaluate company profile and credentials"""
        
        company_profile = vendor_data.get('company_profile', {})
        
        raw_score = 30.0  # Base score
        risk_flags = []
        justification_parts = []
        
        # Years in business
        years_in_business = company_profile.get('years_in_business', 0)
        if years_in_business >= 10:
            raw_score += 20
            justification_parts.append(f"Established company: {years_in_business} years")
        elif years_in_business >= 5:
            raw_score += 15
            justification_parts.append(f"Experienced company: {years_in_business} years")
        elif years_in_business >= 2:
            raw_score += 10
            justification_parts.append(f"Moderate experience: {years_in_business} years")
        else:
            risk_flags.append("Limited business experience")
            justification_parts.append(f"New company: {years_in_business} years")
        
        # Financial capacity
        financial_capacity = company_profile.get('financial_capacity', {})
        annual_turnover = financial_capacity.get('annual_turnover', 0)
        required_turnover = tender_requirements.get('min_annual_turnover', 0)
        
        if required_turnover > 0 and annual_turnover >= required_turnover:
            raw_score += 20
            justification_parts.append("Meets financial capacity requirements")
        elif annual_turnover > 0:
            turnover_ratio = annual_turnover / max(required_turnover, 1)
            if turnover_ratio >= 0.8:
                raw_score += 15
                justification_parts.append("Adequate financial capacity")
            else:
                risk_flags.append("Below required financial capacity")
                raw_score += 5
        else:
            risk_flags.append("Financial capacity not disclosed")
        
        # Industry experience
        industry_experience = company_profile.get('industry_experience', [])
        relevant_experience = [exp for exp in industry_experience 
                             if any(keyword in exp.lower() 
                                  for keyword in tender_requirements.get('relevant_keywords', []))]
        
        if relevant_experience:
            raw_score += 15
            justification_parts.append(f"Relevant industry experience: {len(relevant_experience)} projects")
        else:
            risk_flags.append("Limited relevant industry experience")
        
        # Geographic presence
        locations = company_profile.get('locations', [])
        tender_location = tender_requirements.get('location', '')
        
        if tender_location and any(tender_location.lower() in loc.lower() for loc in locations):
            raw_score += 10
            justification_parts.append("Local presence")
        elif locations:
            raw_score += 5
            justification_parts.append("Multi-location presence")
        
        # Quality certifications
        certifications = company_profile.get('certifications', [])
        quality_certs = [cert for cert in certifications 
                        if any(keyword in cert.lower() 
                              for keyword in ['iso', 'quality', 'cmmi', 'six sigma'])]
        
        if quality_certs:
            raw_score += 5
            justification_parts.append(f"Quality certifications: {len(quality_certs)}")
        
        raw_score = max(0, min(100, raw_score))
        weighted_score = raw_score * self.weights['company_profile']
        
        return CriteriaScore(
            raw_score=raw_score,
            weighted_score=weighted_score,
            confidence=0.7,
            justification=" | ".join(justification_parts) or "Company profile evaluated",
            risk_flags=risk_flags
        )
    
    def _evaluate_methodology(self, vendor_data: Dict[str, Any], 
                            tender_requirements: Dict[str, Any],
                            context_data: Optional[Dict[str, Any]]) -> CriteriaScore:
        """Evaluate project methodology and approach"""
        
        methodology = vendor_data.get('methodology', {})
        
        raw_score = 35.0  # Base score
        risk_flags = []
        justification_parts = []
        
        # Project approach
        approach = methodology.get('approach', '')
        if approach:
            approach_length = len(approach.split())
            if approach_length >= 200:
                raw_score += 25
                justification_parts.append("Detailed methodology provided")
            elif approach_length >= 100:
                raw_score += 20
                justification_parts.append("Good methodology description")
            elif approach_length >= 50:
                raw_score += 15
                justification_parts.append("Basic methodology provided")
            else:
                risk_flags.append("Insufficient methodology detail")
                raw_score += 5
        else:
            risk_flags.append("No methodology provided")
        
        # Risk management
        risk_management = methodology.get('risk_management', '')
        if risk_management:
            raw_score += 15
            justification_parts.append("Risk management plan included")
        else:
            risk_flags.append("No risk management plan")
        
        # Quality assurance
        quality_assurance = methodology.get('quality_assurance', '')
        if quality_assurance:
            raw_score += 10
            justification_parts.append("Quality assurance process defined")
        
        # Project phases
        phases = methodology.get('phases', [])
        if phases and len(phases) >= 3:
            raw_score += 10
            justification_parts.append(f"Well-structured approach: {len(phases)} phases")
        elif phases:
            raw_score += 5
            justification_parts.append("Basic project structure")
        
        # Innovation/unique approach
        innovation = methodology.get('innovation', '')
        if innovation:
            raw_score += 5
            justification_parts.append("Innovative approach described")
        
        raw_score = max(0, min(100, raw_score))
        weighted_score = raw_score * self.weights['methodology']
        
        return CriteriaScore(
            raw_score=raw_score,
            weighted_score=weighted_score,
            confidence=0.6,
            justification=" | ".join(justification_parts) or "Methodology evaluated",
            risk_flags=risk_flags
        )
    
    def _evaluate_credentials(self, vendor_data: Dict[str, Any], 
                            tender_requirements: Dict[str, Any],
                            context_data: Optional[Dict[str, Any]]) -> CriteriaScore:
        """Evaluate team credentials and qualifications"""
        
        credentials = vendor_data.get('credentials', {})
        
        raw_score = 40.0  # Base score
        risk_flags = []
        justification_parts = []
        
        # Team composition
        team_members = credentials.get('team_members', [])
        required_roles = tender_requirements.get('required_roles', [])
        
        if team_members:
            role_coverage = 0
            for required_role in required_roles:
                if any(required_role.lower() in member.get('role', '').lower() 
                      for member in team_members):
                    role_coverage += 1
            
            if required_roles:
                coverage_ratio = role_coverage / len(required_roles)
                raw_score += coverage_ratio * 25
                justification_parts.append(f"Role coverage: {coverage_ratio:.1%}")
            else:
                raw_score += 15
                justification_parts.append(f"Team size: {len(team_members)} members")
        else:
            risk_flags.append("No team information provided")
        
        # Educational qualifications
        education_score = 0
        for member in team_members:
            education = member.get('education', '').lower()
            if any(qual in education for qual in ['phd', 'doctorate']):
                education_score += 3
            elif any(qual in education for qual in ['master', 'mtech', 'mba']):
                education_score += 2
            elif any(qual in education for qual in ['bachelor', 'btech', 'be']):
                education_score += 1
        
        raw_score += min(15, education_score)
        if education_score > 0:
            justification_parts.append("Qualified team members")
        
        # Experience
        total_experience = sum(member.get('experience_years', 0) for member in team_members)
        avg_experience = total_experience / len(team_members) if team_members else 0
        
        if avg_experience >= 10:
            raw_score += 15
            justification_parts.append(f"Highly experienced team: {avg_experience:.1f} years avg")
        elif avg_experience >= 5:
            raw_score += 10
            justification_parts.append(f"Experienced team: {avg_experience:.1f} years avg")
        elif avg_experience >= 2:
            raw_score += 5
            justification_parts.append(f"Moderate experience: {avg_experience:.1f} years avg")
        else:
            risk_flags.append("Limited team experience")
        
        # Certifications
        certifications = credentials.get('certifications', [])
        if certifications:
            raw_score += min(5, len(certifications))
            justification_parts.append(f"Professional certifications: {len(certifications)}")
        
        raw_score = max(0, min(100, raw_score))
        weighted_score = raw_score * self.weights['credentials']
        
        return CriteriaScore(
            raw_score=raw_score,
            weighted_score=weighted_score,
            confidence=0.7,
            justification=" | ".join(justification_parts) or "Credentials evaluated",
            risk_flags=risk_flags
        )
    
    def _evaluate_references(self, vendor_data: Dict[str, Any], 
                           tender_requirements: Dict[str, Any],
                           context_data: Optional[Dict[str, Any]]) -> CriteriaScore:
        """Evaluate client references and past performance"""
        
        references = vendor_data.get('references', [])
        
        raw_score = 30.0  # Base score
        risk_flags = []
        justification_parts = []
        
        if not references:
            risk_flags.append("No references provided")
            raw_score = 20
            justification_parts.append("No client references")
        else:
            # Number of references
            ref_count = len(references)
            if ref_count >= 5:
                raw_score += 20
                justification_parts.append(f"Multiple references: {ref_count}")
            elif ref_count >= 3:
                raw_score += 15
                justification_parts.append(f"Good references: {ref_count}")
            elif ref_count >= 1:
                raw_score += 10
                justification_parts.append(f"Limited references: {ref_count}")
            
            # Quality of references
            quality_score = 0
            for ref in references:
                # Government/PSU references get higher weightage
                client_type = ref.get('client_type', '').lower()
                if any(keyword in client_type for keyword in ['government', 'psu', 'public']):
                    quality_score += 3
                elif 'private' in client_type:
                    quality_score += 2
                else:
                    quality_score += 1
                
                # Project value consideration
                project_value = ref.get('project_value', 0)
                tender_value = tender_requirements.get('estimated_value', 0)
                if tender_value > 0 and project_value >= tender_value * 0.5:
                    quality_score += 2
                
                # Recent projects get higher score
                completion_date = ref.get('completion_date', '')
                if completion_date:
                    try:
                        completion = datetime.strptime(completion_date, '%Y-%m-%d')
                        if completion >= datetime.now() - timedelta(days=365*2):  # Within 2 years
                            quality_score += 2
                        elif completion >= datetime.now() - timedelta(days=365*5):  # Within 5 years
                            quality_score += 1
                    except:
                        pass
            
            raw_score += min(30, quality_score)
            justification_parts.append("Reference quality assessed")
            
            # Performance ratings
            avg_rating = np.mean([ref.get('performance_rating', 3) for ref in references])
            if avg_rating >= 4.5:
                raw_score += 20
                justification_parts.append(f"Excellent ratings: {avg_rating:.1f}/5")
            elif avg_rating >= 4.0:
                raw_score += 15
                justification_parts.append(f"Good ratings: {avg_rating:.1f}/5")
            elif avg_rating >= 3.5:
                raw_score += 10
                justification_parts.append(f"Average ratings: {avg_rating:.1f}/5")
            else:
                risk_flags.append(f"Below average ratings: {avg_rating:.1f}/5")
        
        raw_score = max(0, min(100, raw_score))
        weighted_score = raw_score * self.weights['references']
        
        return CriteriaScore(
            raw_score=raw_score,
            weighted_score=weighted_score,
            confidence=0.8,
            justification=" | ".join(justification_parts) or "References evaluated",
            risk_flags=risk_flags
        )
    
    def _evaluate_timeline(self, vendor_data: Dict[str, Any], 
                         tender_requirements: Dict[str, Any],
                         context_data: Optional[Dict[str, Any]]) -> CriteriaScore:
        """Evaluate project timeline and delivery schedule"""
        
        timeline = vendor_data.get('timeline', {})
        
        raw_score = 50.0  # Base score
        risk_flags = []
        justification_parts = []
        
        # Proposed delivery time
        proposed_duration = timeline.get('duration_days', 0)
        required_duration = tender_requirements.get('max_duration_days', 0)
        
        if proposed_duration <= 0:
            risk_flags.append("No timeline provided")
            raw_score = 20
            justification_parts.append("Missing project timeline")
        elif required_duration > 0:
            duration_ratio = proposed_duration / required_duration
            
            if duration_ratio <= 0.8:
                # Very fast delivery - might be unrealistic
                if duration_ratio <= 0.5:
                    risk_flags.append("Unrealistically fast delivery")
                    raw_score -= 20
                else:
                    raw_score += 15
                    justification_parts.append("Fast delivery proposed")
            elif duration_ratio <= 1.0:
                raw_score += 25
                justification_parts.append("Within required timeframe")
            elif duration_ratio <= 1.2:
                raw_score += 10
                justification_parts.append("Slightly longer than required")
            else:
                risk_flags.append("Exceeds required timeline")
                raw_score -= 10
        else:
            # No specific requirement, assess reasonableness
            if proposed_duration <= 30:
                risk_flags.append("Very short timeline")
            elif proposed_duration <= 365:
                raw_score += 15
                justification_parts.append(f"Reasonable timeline: {proposed_duration} days")
            else:
                risk_flags.append("Very long timeline")
        
        # Project milestones
        milestones = timeline.get('milestones', [])
        if milestones:
            if len(milestones) >= 5:
                raw_score += 15
                justification_parts.append(f"Well-defined milestones: {len(milestones)}")
            elif len(milestones) >= 3:
                raw_score += 10
                justification_parts.append(f"Good milestone planning: {len(milestones)}")
            else:
                raw_score += 5
                justification_parts.append("Basic milestone planning")
        else:
            risk_flags.append("No milestone planning")
        
        # Resource allocation
        resource_plan = timeline.get('resource_allocation', '')
        if resource_plan:
            raw_score += 10
            justification_parts.append("Resource allocation planned")
        
        raw_score = max(0, min(100, raw_score))
        weighted_score = raw_score * self.weights['timeline']
        
        return CriteriaScore(
            raw_score=raw_score,
            weighted_score=weighted_score,
            confidence=0.8,
            justification=" | ".join(justification_parts) or "Timeline evaluated",
            risk_flags=risk_flags
        )
    
    def _assess_overall_risk(self, criteria_scores: Dict[str, CriteriaScore], 
                           vendor_data: Dict[str, Any]) -> RiskLevel:
        """Assess overall risk level based on all criteria"""
        
        total_risk_flags = sum(len(score.risk_flags) for score in criteria_scores.values())
        low_scores = sum(1 for score in criteria_scores.values() if score.raw_score < 50)
        very_low_scores = sum(1 for score in criteria_scores.values() if score.raw_score < 30)
        
        if very_low_scores >= 3 or total_risk_flags >= 10:
            return RiskLevel.CRITICAL
        elif very_low_scores >= 2 or low_scores >= 4 or total_risk_flags >= 6:
            return RiskLevel.HIGH
        elif low_scores >= 2 or total_risk_flags >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _determine_compliance_status(self, criteria_scores: Dict[str, CriteriaScore]) -> ComplianceStatus:
        """Determine overall compliance status"""
        
        compliant_criteria = sum(1 for score in criteria_scores.values() 
                               if score.raw_score >= 70 and not score.risk_flags)
        partial_criteria = sum(1 for score in criteria_scores.values() 
                             if 50 <= score.raw_score < 70)
        non_compliant_criteria = sum(1 for score in criteria_scores.values() 
                                   if score.raw_score < 50)
        
        total_criteria = len(criteria_scores)
        
        if compliant_criteria == total_criteria:
            return ComplianceStatus.COMPLIANT
        elif non_compliant_criteria == 0:
            return ComplianceStatus.PARTIAL
        elif non_compliant_criteria >= total_criteria // 2:
            return ComplianceStatus.NON_COMPLIANT
        else:
            return ComplianceStatus.PARTIAL
    
    def _generate_recommendation(self, overall_score: float, weighted_score: float, 
                               risk_level: RiskLevel, compliance_status: ComplianceStatus) -> str:
        """Generate final recommendation"""
        
        if compliance_status == ComplianceStatus.NON_COMPLIANT or risk_level == RiskLevel.CRITICAL:
            return "REJECT"
        elif weighted_score >= 80 and risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
            return "STRONGLY RECOMMEND"
        elif weighted_score >= 70 and compliance_status == ComplianceStatus.COMPLIANT:
            return "RECOMMEND"
        elif weighted_score >= 60:
            return "CONDITIONALLY RECOMMEND"
        elif weighted_score >= 50:
            return "CONSIDER WITH RESERVATIONS"
        else:
            return "NOT RECOMMENDED"
    
    def _create_error_evaluation(self, vendor_data: Dict[str, Any], error_msg: str) -> VendorEvaluation:
        """Create default evaluation for error cases"""
        
        vendor_id = vendor_data.get('vendor_id', 'unknown')
        vendor_name = vendor_data.get('vendor_name', 'Unknown Vendor')
        
        # Create default criteria scores
        default_score = CriteriaScore(
            raw_score=0.0,
            weighted_score=0.0,
            confidence=0.0,
            justification=f"Evaluation failed: {error_msg}",
            risk_flags=["Evaluation error"]
        )
        
        criteria_scores = {key: default_score for key in self.weights.keys()}
        
        return VendorEvaluation(
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            criteria_scores=criteria_scores,
            overall_score=0.0,
            weighted_score=0.0,
            risk_level=RiskLevel.CRITICAL,
            compliance_status=ComplianceStatus.UNCLEAR,
            recommendation="EVALUATION FAILED",
            evaluation_timestamp=datetime.now().isoformat(),
            evaluator_notes=f"Error during evaluation: {error_msg}"
        )
    
    def compare_vendors(self, evaluations: List[VendorEvaluation]) -> Dict[str, Any]:
        """Compare multiple vendor evaluations"""
        
        if not evaluations:
            return {"error": "No evaluations provided"}
        
        # Sort by weighted score
        sorted_evaluations = sorted(evaluations, key=lambda x: x.weighted_score, reverse=True)
        
        # Calculate statistics
        scores = [eval.weighted_score for eval in evaluations]
        
        comparison = {
            "ranking": [
                {
                    "rank": i + 1,
                    "vendor_name": eval.vendor_name,
                    "vendor_id": eval.vendor_id,
                    "weighted_score": eval.weighted_score,
                    "recommendation": eval.recommendation,
                    "risk_level": eval.risk_level.value
                }
                for i, eval in enumerate(sorted_evaluations)
            ],
            "statistics": {
                "total_vendors": len(evaluations),
                "average_score": np.mean(scores),
                "median_score": np.median(scores),
                "score_range": max(scores) - min(scores),
                "recommended_vendors": len([e for e in evaluations 
                                          if "RECOMMEND" in e.recommendation])
            },
            "top_vendor": {
                "name": sorted_evaluations[0].vendor_name,
                "score": sorted_evaluations[0].weighted_score,
                "recommendation": sorted_evaluations[0].recommendation
            } if sorted_evaluations else None
        }
        
        return comparison
    
    def export_evaluation_report(self, evaluation: VendorEvaluation) -> Dict[str, Any]:
        """Export detailed evaluation report"""
        
        return {
            "vendor_information": {
                "vendor_id": evaluation.vendor_id,
                "vendor_name": evaluation.vendor_name,
                "evaluation_timestamp": evaluation.evaluation_timestamp
            },
            "overall_assessment": {
                "overall_score": evaluation.overall_score,
                "weighted_score": evaluation.weighted_score,
                "risk_level": evaluation.risk_level.value,
                "compliance_status": evaluation.compliance_status.value,
                "final_recommendation": evaluation.recommendation
            },
            "detailed_scores": {
                criterion: {
                    "raw_score": score.raw_score,
                    "weighted_score": score.weighted_score,
                    "weight": self.weights[criterion],
                    "confidence": score.confidence,
                    "justification": score.justification,
                    "risk_flags": score.risk_flags
                }
                for criterion, score in evaluation.criteria_scores.items()
            },
            "risk_analysis": {
                "total_risk_flags": sum(len(score.risk_flags) 
                                      for score in evaluation.criteria_scores.values()),
                "critical_areas": [
                    criterion for criterion, score in evaluation.criteria_scores.items()
                    if score.raw_score < 50 or len(score.risk_flags) >= 2
                ]
            },
            "evaluator_notes": evaluation.evaluator_notes
        }

# Global scorer instance
vendor_scorer = AdvancedVendorScorer()

# Convenience functions for backward compatibility
def score_vendor(price: float, compliance: float, delivery: float) -> float:
    """Simple vendor scoring function for backward compatibility"""
    return 0.5 * compliance + 0.3 * (1/max(price, 1)) + 0.2 * delivery

def evaluate_vendor_comprehensive(vendor_data: Dict[str, Any], 
                                 tender_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive vendor evaluation"""
    evaluation = vendor_scorer.evaluate_vendor_comprehensive(vendor_data, tender_requirements)
    return asdict(evaluation)

def compare_vendors_detailed(vendor_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare multiple vendors"""
    evaluations = [VendorEvaluation(**eval_data) for eval_data in vendor_evaluations]
    return vendor_scorer.compare_vendors(evaluations)
