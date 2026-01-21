"""Pydantic models and type definitions."""
from typing import Annotated, TypedDict, List
from pydantic import BaseModel, Field
from operator import add


class SubmissionCheck(BaseModel):
    """Schema for LLM email classification."""
    is_article_submission: bool = Field(
        description="True if the email content is a request to submit or publish an article/guest post."
    )
    email_type: str = Field(
        description="Type of email: 'article_submission' or 'other' (reserved for future types)"
    )


class AgentState(TypedDict):
    """LangGraph agent state definition."""
    emails: Annotated[List[dict], lambda a, b: b]
    processed_count: Annotated[int, lambda a, b: b]
    replied_count: Annotated[int, lambda a, b: b]
    current_index: Annotated[int, lambda a, b: b]
    errors: Annotated[List[str], add]
    current_email: Annotated[dict, lambda a, b: b]
    classification_result: Annotated[SubmissionCheck, lambda a, b: b]
