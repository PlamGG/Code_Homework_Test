# Support Ticket Triage Agent

Deterministic, tool-augmented AI agent that automates support ticket triage: classifies urgency, extracts structured signals, queries internal runbooks, and decides operational routing.

---

## Quickstart (3 Steps)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Configure OpenAI API Key
# If omitted, system runs seamlessly in deterministic offline evaluation mode
copy .env.example .env

# 3. Run triage across sample tickets
python main.py
```

### CLI Options
```bash
python main.py --ticket TICKET-001    # Run single ticket
python main.py --json                 # Output raw structured JSON
python -m pytest tests/ -v           # Run test suite
```

---

## Sample Ticket Results

| Ticket ID | Scenario / Customer | Urgency | Next Action | Target Team | Key Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TICKET-001** | Free tier, 3x charges ($89.97), demo in 2h, bank dispute threat | **HIGH** | `escalate to human` | Tier-2 Billing | Active financial harm, uncaptured auth timeout, 2-hour deadline. |
| **TICKET-002** | Enterprise (45 seats), HTTP 500 across all users, major client demo today | **CRITICAL** | `escalate to human` | On-call SRE / Tier-3 | 15-min SLA breach risk, regional edge outage, severe deal risk. |
| **TICKET-003** | Pro tier, macOS dark mode inquiry & scheduling feature request | **LOW** | `auto-respond` | Frontline / Product Backlog | Documented workaround (KB-301) provided; logs idea to backlog. |

---

## Project Structure
```
├── data/
│   ├── sample_tickets.json       # Multi-turn customer threads from assignment
│   └── mock_kb.json              # Internal runbooks and SOP articles
├── src/
│   ├── models.py                 # Pydantic schemas (TriageResult, UrgencyEnum, etc.)
│   ├── tools.py                  # Tool definitions (lookup_customer_history, search_kb)
│   ├── prompts.py                # System prompt guiding agent triage logic
│   └── agent.py                  # Two-phase OpenAI tool calling & structured outputs
├── tests/
│   └── test_agent.py             # Automated unit & integration tests
├── main.py                       # CLI application runner
└── writeup.md                    # 1-page architecture, failure modes & evaluation plan
```
