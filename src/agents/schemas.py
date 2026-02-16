import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Dimensions(BaseModel):
    dcm_capability: str  = Field(..., description="One of the 6 DCM capabilities: connected customer, product development, synchronised planning, intelligent supply, smart operations, dynamic fulfillment")
    scor_process: str = Field(..., description="Classification based on the traditional SCOR process")
    scrm_area: Optional[str] = Field(None, description="Type of supply chain risk management addressed, if any")
    problem_description: str = Field(..., description="1 sentence description of the problem statement or research gap addressed by the paper")
    ai_technology_nature: str = Field(..., description="Nature of AI technology used (e.g., machine learning, optimization, simulation)")
    industry_sector: str = Field(..., description="Specific industry or sector of application (e.g., automotive, pharmaceutical, general)")

class FieldEvaluation(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")
    subdimension_scores: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Optional scores per subdimension, e.g., semantic, factual, completeness"
    )
    notes: Optional[List[str]] = Field(default_factory=list, description="Optional list of notes if score < 1")

class EvaluationResult(BaseModel):
    overall_score: Optional[float] = Field(None, description="Average score across fields")
    fields: Dict[str, FieldEvaluation]

    def compute_overall_score(self):
        """Compute overall score as average of field scores."""
        if self.fields:
            self.overall_score = sum(f.score for f in self.fields.values()) / len(self.fields)

