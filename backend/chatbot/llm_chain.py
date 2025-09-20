"""
Enhanced LLM Chain for Tender Evaluation
Incorporates advanced prompt engineering and multi-step reasoning from medical RAG
"""
from langchain_community.chat_models import AzureChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import logging

from backend.config import (
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_DEPLOYMENT_NAME, 
    AZURE_API_VERSION, OPENAI_API_KEY, TEMPERATURE, MAX_TOKENS
)

# Set up logging
logger = logging.getLogger(__name__)

class TenderAnalysisResponse(BaseModel):
    """Structured response for tender analysis"""
    summary: str = Field(description="Brief summary of the analysis")
    key_findings: List[str] = Field(description="Key findings from the document analysis")
    compliance_status: str = Field(description="Compliance status: COMPLIANT, NON_COMPLIANT, or PARTIAL")
    risk_flags: List[str] = Field(description="Identified risk factors")
    recommendations: List[str] = Field(description="Recommendations for evaluators")
    confidence_score: float = Field(description="Confidence score between 0 and 1")

class VendorEvaluationResponse(BaseModel):
    """Structured response for vendor evaluation"""
    vendor_name: str = Field(description="Name of the vendor")
    overall_score: float = Field(description="Overall evaluation score (0-100)")
    criteria_scores: Dict[str, float] = Field(description="Individual criteria scores")
    strengths: List[str] = Field(description="Vendor strengths")
    weaknesses: List[str] = Field(description="Areas for improvement")
    final_recommendation: str = Field(description="RECOMMEND, CONDITIONAL, or REJECT")

class EnhancedLLMChain:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tender_parser = PydanticOutputParser(pydantic_object=TenderAnalysisResponse)
        self.vendor_parser = PydanticOutputParser(pydantic_object=VendorEvaluationResponse)
        
    def _initialize_llm(self):
        """Initialize LLM with fallback options"""
        try:
            # Try Azure OpenAI first
            if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY:
                logger.info("Initializing Azure OpenAI")
                return AzureChatOpenAI(
                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                    openai_api_key=AZURE_OPENAI_KEY,
                    deployment_name=AZURE_DEPLOYMENT_NAME,
                    openai_api_version=AZURE_API_VERSION,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS
                )
        except Exception as e:
            logger.warning(f"Azure OpenAI failed: {e}")
        
        try:
            # Fallback to OpenAI
            if OPENAI_API_KEY:
                logger.info("Initializing OpenAI")
                return ChatOpenAI(
                    openai_api_key=OPENAI_API_KEY,
                    model_name="gpt-4",
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS
                )
        except Exception as e:
            logger.error(f"OpenAI initialization failed: {e}")
            raise Exception("No LLM available. Please configure Azure OpenAI or OpenAI credentials.")

    def analyze_tender_document(self, document_text: str, tender_requirements: Dict[str, Any]) -> TenderAnalysisResponse:
        """
        Analyze tender document for compliance and extract key information
        Enhanced with structured output parsing
        """
        system_prompt = """You are an expert government procurement analyst specializing in tender evaluation.
        Your task is to analyze tender documents for compliance, extract key information, and identify potential risks.
        
        Focus on:
        1. Mandatory requirements compliance
        2. Financial proposal analysis
        3. Technical capability assessment
        4. Risk identification
        5. Document completeness
        
        Be thorough, objective, and provide specific evidence for your assessments."""
        
        human_prompt = f"""
        Analyze the following tender document:
        
        TENDER REQUIREMENTS:
        {json.dumps(tender_requirements, indent=2)}
        
        DOCUMENT CONTENT:
        {document_text}
        
        Provide a comprehensive analysis following this format:
        {self.tender_parser.get_format_instructions()}
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm(messages)
            parsed_response = self.tender_parser.parse(response.content)
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error in tender analysis: {e}")
            # Return default response on error
            return TenderAnalysisResponse(
                summary="Error occurred during analysis",
                key_findings=["Analysis failed due to technical error"],
                compliance_status="UNKNOWN",
                risk_flags=["Technical analysis error"],
                recommendations=["Manual review required"],
                confidence_score=0.0
            )

    def evaluate_vendor_proposal(self, vendor_data: Dict[str, Any], evaluation_criteria: Dict[str, Any], 
                                context_chunks: List[str]) -> VendorEvaluationResponse:
        """
        Comprehensive vendor evaluation with multi-criteria analysis
        """
        context = "\n".join(context_chunks)
        
        system_prompt = """You are a senior procurement evaluation specialist with expertise in government tenders.
        
        Your responsibilities:
        1. Evaluate vendor proposals against specific criteria
        2. Assign scores based on evidence and compliance
        3. Identify strengths and improvement areas
        4. Provide clear recommendations with justification
        
        Scoring Guidelines:
        - 90-100: Exceptional, exceeds requirements significantly
        - 80-89: Good, meets requirements with some added value
        - 70-79: Satisfactory, meets basic requirements
        - 60-69: Below average, meets some requirements
        - Below 60: Poor, fails to meet key requirements
        
        Be fair, consistent, and evidence-based in your evaluation."""
        
        human_prompt = f"""
        Evaluate the following vendor proposal:
        
        VENDOR INFORMATION:
        {json.dumps(vendor_data, indent=2)}
        
        EVALUATION CRITERIA:
        {json.dumps(evaluation_criteria, indent=2)}
        
        SUPPORTING CONTEXT:
        {context}
        
        Provide a detailed evaluation following this format:
        {self.vendor_parser.get_format_instructions()}
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm(messages)
            parsed_response = self.vendor_parser.parse(response.content)
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error in vendor evaluation: {e}")
            # Return default response on error
            return VendorEvaluationResponse(
                vendor_name=vendor_data.get("vendor_name", "Unknown"),
                overall_score=0.0,
                criteria_scores={},
                strengths=[],
                weaknesses=["Evaluation failed due to technical error"],
                final_recommendation="REJECT"
            )

    def generate_comparative_analysis(self, vendors: List[Dict[str, Any]]) -> str:
        """
        Generate comparative analysis of multiple vendors
        """
        system_prompt = """You are conducting a comparative analysis of tender proposals.
        Create a comprehensive comparison highlighting:
        1. Relative strengths and weaknesses
        2. Value proposition differences
        3. Risk assessment comparison
        4. Final ranking recommendations
        
        Be objective and provide clear reasoning for recommendations."""
        
        human_prompt = f"""
        Compare the following vendor proposals and provide a comprehensive analysis:
        
        VENDORS:
        {json.dumps(vendors, indent=2)}
        
        Provide:
        1. Executive summary of key differences
        2. Detailed comparison by criteria
        3. Risk analysis for each vendor
        4. Final recommendation and ranking
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error in comparative analysis: {e}")
            return f"Comparative analysis failed: {str(e)}"

    def answer_question(self, question: str, context_chunks: List[str], tender_context: Optional[Dict] = None) -> str:
        """
        Answer specific questions about tenders with enhanced context awareness
        """
        context = "\n".join(context_chunks)
        
        system_prompt = """You are a knowledgeable assistant specializing in government procurement and tender processes.
        
        Guidelines:
        1. Provide accurate, factual answers based on the provided context
        2. If information is not available in the context, clearly state this
        3. For regulatory questions, emphasize compliance requirements
        4. For evaluation questions, explain criteria and methodology
        5. Always maintain professional tone appropriate for government context"""
        
        context_info = ""
        if tender_context:
            context_info = f"\nTENDER CONTEXT:\n{json.dumps(tender_context, indent=2)}\n"
        
        human_prompt = f"""
        {context_info}
        RELEVANT INFORMATION:
        {context}
        
        QUESTION: {question}
        
        Please provide a comprehensive answer based on the available information.
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"I apologize, but I encountered an error while processing your question: {str(e)}"

# Global instance
llm_chain = EnhancedLLMChain()

# Convenience functions for backward compatibility
def generate_answer(question: str, context_chunks: List[str], tender_context: Optional[Dict] = None) -> str:
    """Generate answer to question with context"""
    return llm_chain.answer_question(question, context_chunks, tender_context)

def analyze_tender_document(document_text: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze tender document and return structured response"""
    result = llm_chain.analyze_tender_document(document_text, requirements)
    return result.dict()

def evaluate_vendor(vendor_data: Dict[str, Any], criteria: Dict[str, Any], context: List[str]) -> Dict[str, Any]:
    """Evaluate vendor proposal and return structured response"""
    result = llm_chain.evaluate_vendor_proposal(vendor_data, criteria, context)
    return result.dict()
