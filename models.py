"""Pydantic models and type definitions."""
from typing import Annotated, TypedDict, List, Optional
from pydantic import BaseModel, Field
from operator import add


class ClassificationResult(BaseModel):
    """Schema for LLM email classification response."""
    match: bool = Field(
        description="True if the email matches this classification"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1"
    )
    reasoning: str = Field(
        description="Brief explanation of the classification decision"
    )


class Classification(BaseModel):
    """Configuration for a single email classification."""
    name: str = Field(description="Unique identifier for this classification")
    priority: int = Field(description="Priority order (lower number = higher priority)")
    description: str = Field(description="Human-readable description")
    classification_prompt: str = Field(description="Path to prompt file")
    action: str = Field(description="Action to take: reply, skip, forward, label")
    reply_template: Optional[str] = Field(default=None, description="Path to reply template (if action=reply)")


class EmailClassification(BaseModel):
    """Result of classifying an email."""
    classification_name: str = Field(description="Name of the matched classification")
    confidence: float = Field(description="Confidence score")
    reasoning: str = Field(description="Reasoning for the classification")
    action: str = Field(description="Action to take")
    reply_template: Optional[str] = Field(default=None, description="Reply template path if applicable")


class AgentState(TypedDict):
    """LangGraph agent state definition."""
    emails: Annotated[List[dict], lambda a, b: b]
    processed_count: Annotated[int, lambda a, b: b]
    replied_count: Annotated[int, lambda a, b: b]
    current_index: Annotated[int, lambda a, b: b]
    errors: Annotated[List[str], add]
    current_email: Annotated[dict, lambda a, b: b]
    classification_result: Annotated[Optional[EmailClassification], lambda a, b: b]
