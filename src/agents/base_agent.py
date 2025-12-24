# src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.schemas.evidence import EvidenceExtraction, EvidenceItem, SourceSpan
from src.schemas.claims import AgentClaims, Claim, ClaimDirection, Gap
from src.config.settings import settings

class BaseAgent(ABC):
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.temperature = settings.agent_temperature
        
    @abstractmethod
    def get_system_prompt_evidence(self) -> str:
        """Get system prompt for evidence extraction"""
        pass
        
    @abstractmethod
    def get_system_prompt_claims(self) -> str:
        """Get system prompt for claims generation"""
        pass
    
    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_llm_with_schema(self, messages: List[Dict], 
                              response_format: Dict) -> Dict:
        """Call OpenAI with strict JSON schema"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format=response_format,
                seed=42  # For reproducibility
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
                
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")
    
    def extract_evidence(self, event_id: str, incident_text: str) -> EvidenceExtraction:
        """Extract evidence with structured output"""
        # Define JSON schema for evidence extraction
        evidence_schema = {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "format": "uuid"},
                "agent_id": {"type": "string", "enum": ["benign", "malicious", "skeptic"]},
                "evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {"type": "string", "format": "uuid"},
                            "type": {"type": "string", "enum": [et.value for et in EvidenceType]},
                            "value": {"type": "string"},
                            "normalized": {
                                "type": "object",
                                "properties": {
                                    "key": {"type": "string"},
                                    "value": {"type": "string"}
                                },
                                "required": ["key", "value"]
                            },
                            "source_spans": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "start_char": {"type": "integer", "minimum": 0},
                                        "end_char": {"type": "integer", "minimum": 0},
                                        "quote": {"type": "string"}
                                    },
                                    "required": ["start_char", "end_char", "quote"]
                                }
                            },
                            "extraction_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "notes": {"type": ["string", "null"]}
                        },
                        "required": ["type", "value", "source_spans", "extraction_confidence"]
                    }
                }
            },
            "required": ["event_id", "agent_id", "evidence"]
        }
        
        messages = [
            {"role": "system", "content": self.get_system_prompt_evidence()},
            {"role": "user", "content": f"Incident Text:\n{incident_text}\n\nExtract evidence with exact quotes from the text above."}
        ]
        
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "evidence_extraction",
                "schema": evidence_schema,
                "strict": True
            }
        }
        
        result = self._call_llm_with_schema(messages, response_format)
        result["event_id"] = event_id
        result["agent_id"] = self.agent_id
        
        # Validate and normalize evidence
        for item in result["evidence"]:
            # Normalize value
            normalized_value = item["value"].lower().strip()
            item["normalized"] = {
                "key": item["type"],
                "value": normalized_value
            }
        
        return EvidenceExtraction(**result)
    
    def generate_claims(self, event_id: str, incident_text: str, 
                       evidence_extraction: EvidenceExtraction) -> AgentClaims:
        """Generate claims grounded in evidence"""
        # Define JSON schema for claims
        claims_schema = {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "format": "uuid"},
                "agent_id": {"type": "string", "enum": ["benign", "malicious", "skeptic"]},
                "stance": {"type": "string", "enum": ["BENIGN_HYPOTHESIS", "MALICIOUS_HYPOTHESIS", "SKEPTICAL_HYPOTHESIS"]},
                "claims": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim_id": {"type": "string", "format": "uuid"},
                            "summary": {"type": "string"},
                            "direction": {"type": "string", "enum": [cd.value for cd in ClaimDirection]},
                            "supporting_evidence_ids": {
                                "type": "array",
                                "items": {"type": "string", "format": "uuid"}
                            },
                            "counter_evidence_ids": {
                                "type": "array", 
                                "items": {"type": "string", "format": "uuid"}
                            },
                            "claim_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "assumptions": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["summary", "direction", "claim_confidence"]
                    }
                },
                "agent_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "gaps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "gap": {"type": "string"},
                            "why_it_matters": {"type": "string"}
                        },
                        "required": ["gap", "why_it_matters"]
                    }
                }
            },
            "required": ["stance", "claims", "agent_confidence"]
        }
        
        # Prepare evidence list for context
        evidence_list = [
            {
                "evidence_id": str(item.evidence_id),
                "type": item.type.value,
                "value": item.value,
                "normalized": item.normalized
            }
            for item in evidence_extraction.evidence
        ]
        
        messages = [
            {"role": "system", "content": self.get_system_prompt_claims()},
            {"role": "user", "content": f"""Incident Text:
{incident_text}

Available Evidence (cite by evidence_id only):
{json.dumps(evidence_list, indent=2)}

Generate claims grounded in the evidence above. You may contradict your initial stance if evidence requires it."""}
        ]
        
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "agent_claims",
                "schema": claims_schema,
                "strict": True
            }
        }
        
        result = self._call_llm_with_schema(messages, response_format)
        result["event_id"] = event_id
        result["agent_id"] = self.agent_id
        
        return AgentClaims(**result)