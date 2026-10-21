import json
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def _load_kb() -> List[Dict[str, Any]]:
    kb_path = DATA_DIR / "mock_kb.json"
    if kb_path.exists():
        with open(kb_path, "r", encoding="utf-8") as f:
            return json.load(f).get("articles", [])
    return []

# Mock customer database
MOCK_CUSTOMERS = {
    "CUST-1001": {
        "customer_id": "CUST-1001",
        "name": "Alex Miller",
        "plan": "Free Tier",
        "tenure_months": 4,
        "seats": 1,
        "total_spend": "$0.00",
        "billing_status": "Upgrade Attempted - 3 Failed Authorizations",
        "recent_transactions": [
            {"id": "txn_101", "amount": "$29.99", "status": "pending_capture", "gateway_code": "auth_timeout"},
            {"id": "txn_102", "amount": "$29.99", "status": "pending_capture", "gateway_code": "auth_timeout"},
            {"id": "txn_103", "amount": "$29.99", "status": "pending_capture", "gateway_code": "auth_timeout"}
        ],
        "open_tickets": 1,
        "past_tickets": 0,
        "sla_tier": "Standard"
    },
    "CUST-2002": {
        "customer_id": "CUST-2002",
        "name": "Siam Enterprise Co., Ltd.",
        "plan": "Enterprise",
        "tenure_months": 8,
        "seats": 45,
        "total_spend": "$24,500.00",
        "region": "ap-southeast-1 (Bangkok / Singapore)",
        "account_manager": "Somchai P.",
        "sla_tier": "Critical Priority (15m response)",
        "open_tickets": 1,
        "past_tickets": 2,
        "system_status_note": "Internal alerts show AP-Southeast Edge POP packet loss spiking since 40m ago"
    },
    "CUST-3003": {
        "customer_id": "CUST-3003",
        "name": "Morgan Davis",
        "plan": "Pro",
        "tenure_months": 5,
        "seats": 1,
        "total_spend": "$149.95",
        "activity": "Daily active user, zero past incidents",
        "client_env": "macOS Sonoma, App v4.2.1",
        "sla_tier": "Standard",
        "open_tickets": 1,
        "past_tickets": 0
    }
}

def lookup_customer_history(customer_id: str) -> Dict[str, Any]:
    """
    Look up customer account details, subscription tier, billing transactions, SLA level, and past ticket history.
    """
    if customer_id in MOCK_CUSTOMERS:
        return {"status": "success", "data": MOCK_CUSTOMERS[customer_id]}
    return {"status": "not_found", "message": f"Customer ID {customer_id} not found in database."}

def search_knowledge_base(query: str) -> Dict[str, Any]:
    """
    Search the internal knowledge base for relevant FAQs, troubleshooting runbooks, policies, and known issues.
    """
    articles = _load_kb()
    query_tokens = query.lower().split()
    results = []
    
    for art in articles:
        text_corpus = f"{art.get('title', '')} {art.get('category', '')} {' '.join(art.get('tags', []))} {art.get('content', '')}".lower()
        score = sum(1 for token in query_tokens if token in text_corpus)
        if score > 0:
            results.append({"article": art, "score": score})
            
    results.sort(key=lambda x: x["score"], reverse=True)
    matched = [r["article"] for r in results[:2]]
    
    return {
        "status": "success",
        "query": query,
        "match_count": len(matched),
        "results": matched
    }

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_customer_history",
            "description": "Look up customer account details, subscription plan, billing status, transaction history, and SLA tier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique customer identifier, e.g., CUST-1001"
                    }
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the internal knowledge base for SOPs, troubleshooting guides, and incident runbooks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search terms or keywords representing the technical or billing problem (e.g. 'error 500 enterprise asia', 'pending charge failed upgrade', 'dark mode macos')"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

TOOL_REGISTRY = {
    "lookup_customer_history": lookup_customer_history,
    "search_knowledge_base": search_knowledge_base
}
