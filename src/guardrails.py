import re
from typing import Tuple, Optional

# Known prompt injection signatures and system-override attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"system\s+prompt\s+override",
    r"disregard\s+guidelines",
    r"act\s+as\s+(an?\s+)?unrestricted",
    r"repeat\s+after\s+me",
    r"give\s+me\s+super\s*admin"
]

# Hallucination markers: unauthorized financial promises made without human approval
HALLUCINATION_PATTERNS = [
    r"i\s+have\s+(processed|issued|sent)\s+a?\s*(full\s+)?refund",
    r"your\s+money\s+has\s+been\s+refunded",
    r"we\s+have\s+credited\s+your\s+account\s+with\s+\$",
    r"100%\s+guaranteed\s+to\s+be\s+fixed\s+by"
]

def check_input_guardrail(text: str) -> Tuple[bool, Optional[str]]:
    """
    Checks incoming customer messages for security risks like prompt injection or spam.
    Returns (is_flagged, reason).
    """
    cleaned = text.strip()
    
    # 1. Spam / Gibberish detection (empty, purely symbols, or minimal characters)
    if len(cleaned) < 4 and not any(c.isalnum() for c in cleaned):
        return True, "Spam / Gibberish Input: message is too short or devoid of semantic content."

    # 2. Prompt Injection detection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return True, f"Security Warning: Prompt injection pattern detected ('{pattern}')."

    return False, None

def check_output_guardrail(recommended_response: str) -> Tuple[bool, Optional[str]]:
    """
    Validates agent response to ensure it does not hallucinate unauthorized financial or legal commitments.
    Returns (is_flagged, reason).
    """
    for pattern in HALLUCINATION_PATTERNS:
        if re.search(pattern, recommended_response, re.IGNORECASE):
            return True, f"Compliance Violation: Unauthorized financial guarantee detected ('{pattern}')."
            
    return False, None
