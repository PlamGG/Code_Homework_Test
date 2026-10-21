from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SentimentLevel(str, Enum):
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"

class NextActionType(str, Enum):
    AUTO_RESPOND = "auto-respond"
    ROUTE_TO_SPECIALIST = "route to specialist"
    ESCALATE_TO_HUMAN = "escalate to human"

class TicketMessage(BaseModel):
    time_offset: str
    content: str

class TicketInput(BaseModel):
    id: str
    customer_id: str
    customer_info: str
    messages: List[TicketMessage]

class ToolCallLog(BaseModel):
    tool_name: str
    arguments: dict
    result_summary: str

class TriageResult(BaseModel):
    ticket_id: str
    urgency: UrgencyLevel = Field(..., description="Calculated ticket urgency: critical, high, medium, low")
    product: str = Field(..., description="Affected product, feature, or platform area")
    issue_type: str = Field(..., description="Category: Billing/Payment, Infrastructure/Outage, UI/Bug, Feature Request, Account")
    customer_sentiment: SentimentLevel = Field(..., description="Overall emotional state of the customer")
    summary: str = Field(..., description="Concise multi-turn thread summary highlighting the root conflict and urgency triggers")
    next_action: NextActionType = Field(..., description="Decision: auto-respond, route to specialist, or escalate to human")
    target_team_or_tier: Optional[str] = Field(None, description="E.g., On-call SRE / DevOps, Tier-2 Billing, Frontline Support, Jira Product Backlog")
    justification: str = Field(..., description="Reasoning based on SLA, customer tier, sentiment, and financial/business impact")
    recommended_response: str = Field(..., description="Draft response or handover note based on retrieved knowledge base and policy")
    tools_used: List[ToolCallLog] = Field(default_factory=list, description="Audit trail of tools executed during triage")
    is_flagged_by_guardrail: bool = Field(default=False, description="Flagged if input violates security or output requires human compliance review")
    guardrail_notes: Optional[str] = Field(default=None, description="Security or compliance audit details if flagged")
