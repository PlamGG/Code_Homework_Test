import json
from typing import List
from openai import OpenAI
from src.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
from src.models import (
    TicketInput,
    TriageResult,
    ToolCallLog,
    UrgencyLevel,
    SentimentLevel,
    NextActionType
)
from src.tools import TOOL_SCHEMAS, TOOL_REGISTRY, lookup_customer_history, search_knowledge_base
from src.prompts import TRIAGE_SYSTEM_PROMPT
from src.guardrails import check_input_guardrail, check_output_guardrail

class SupportTriageAgent:
    def __init__(self, model: str = OPENAI_MODEL, api_key: str = OPENAI_API_KEY, base_url: str = OPENAI_BASE_URL):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        if api_key:
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self.client = OpenAI(**kwargs)
        else:
            self.client = None

    def _execute_mock_fallback(self, ticket: TicketInput) -> TriageResult:
        """
        Deterministic, rule-based fallback emulator when OPENAI_API_KEY is not configured.
        Guarantees that test suites and offline review runs still execute full tool calls and verification.
        """
        tool_logs: List[ToolCallLog] = []
        
        # 1. Customer history tool
        cust_hist = lookup_customer_history(ticket.customer_id)
        tool_logs.append(ToolCallLog(
            tool_name="lookup_customer_history",
            arguments={"customer_id": ticket.customer_id},
            result_summary=f"Plan: {cust_hist.get('data', {}).get('plan', 'Unknown')}, SLA: {cust_hist.get('data', {}).get('sla_tier', 'Standard')}"
        ))

        # 2. Extract context & KB search
        combined_text = " ".join([m.content for m in ticket.messages]).lower()
        
        # Outage / Critical Incident
        if any(k in combined_text for k in ["error 500", "502", "outage", "ล่ม", "เข้าไม่ได้", "production halted", "frozen", "bad gateway"]):
            query = "error 500 outage enterprise asia"
            kb_res = search_knowledge_base(query)
            tool_logs.append(ToolCallLog(
                tool_name="search_knowledge_base",
                arguments={"query": query},
                result_summary=f"Matched {kb_res.get('match_count')} articles (Top: {kb_res.get('results', [{}])[0].get('title', 'None')})"
            ))
            return TriageResult(
                ticket_id=ticket.id,
                urgency=UrgencyLevel.CRITICAL,
                product="Core Web Platform & Production Gateway",
                issue_type="Infrastructure Outage / Service Degradation",
                customer_sentiment=SentimentLevel.VERY_NEGATIVE,
                summary=f"Severe outage or platform downtime reported: '{ticket.messages[-1].content[:100]}'",
                next_action=NextActionType.ESCALATE_TO_HUMAN,
                target_team_or_tier="On-call SRE / Tier-3 Infrastructure Incident Response",
                justification="Service stoppage impacting production operations or multi-user access requiring immediate SRE triage.",
                recommended_response="Dispatch incident response team, inspect regional gateway/API health, and notify account owners.",
                tools_used=tool_logs
            )
        # Billing / Unauthorized Charges
        elif any(k in combined_text for k in ["charge", "payment", "upgrade", "ตัดเงิน", "คืนเงิน", "refund", "dispute", "บัตรเครดิต", "invoice"]):
            query = "pending charge failed upgrade dispute"
            kb_res = search_knowledge_base(query)
            tool_logs.append(ToolCallLog(
                tool_name="search_knowledge_base",
                arguments={"query": query},
                result_summary=f"Matched {kb_res.get('match_count')} articles (Top: {kb_res.get('results', [{}])[0].get('title', 'None')})"
            ))
            return TriageResult(
                ticket_id=ticket.id,
                urgency=UrgencyLevel.HIGH,
                product="Billing & Subscription Management",
                issue_type="Billing / Payment Dispute",
                customer_sentiment=SentimentLevel.VERY_NEGATIVE,
                summary=f"Billing discrepancy or unauthorized charge inquiry: '{ticket.messages[-1].content[:100]}'",
                next_action=NextActionType.ESCALATE_TO_HUMAN,
                target_team_or_tier="Tier-2 Billing Operations & Retention",
                justification="Direct financial impact or payment authorization discrepancy requiring manual ledger audit.",
                recommended_response="Acknowledge the billing query, verify recent transaction status with payment gateway, and resolve holds/refunds.",
                tools_used=tool_logs
            )
        # Security Threat / Hacking
        elif any(k in combined_text for k in ["hack", "hacked", "brute force", "russia", "โดนแฮก", "2fa", "unauthorized login", "lock account"]):
            query = "account security unauthorized login 2fa"
            kb_res = search_knowledge_base(query)
            tool_logs.append(ToolCallLog(
                tool_name="search_knowledge_base",
                arguments={"query": query},
                result_summary=f"Matched {kb_res.get('match_count')} articles (Top: {kb_res.get('results', [{}])[0].get('title', 'None')})"
            ))
            return TriageResult(
                ticket_id=ticket.id,
                urgency=UrgencyLevel.HIGH,
                product="Identity & Authentication Security",
                issue_type="Security / Account Takeover Threat",
                customer_sentiment=SentimentLevel.NEGATIVE,
                summary=f"Suspected account compromise or suspicious authentication activity reported.",
                next_action=NextActionType.ESCALATE_TO_HUMAN,
                target_team_or_tier="Security Operations / Identity Support",
                justification="Potential credential compromise or unauthorized access requiring immediate session revocation and identity verification.",
                recommended_response="Temporarily lock sensitive actions, terminate active sessions, and issue a secure password reset link.",
                tools_used=tool_logs
            )
        # Bug / Technical Glitch
        elif any(k in combined_text for k in ["bug", "ไม่เซฟ", "กระพริบ", "glitch", "error", "ค้าง"]):
            query = "ui defect button save bug"
            kb_res = search_knowledge_base(query)
            tool_logs.append(ToolCallLog(
                tool_name="search_knowledge_base",
                arguments={"query": query},
                result_summary=f"Matched {kb_res.get('match_count')} articles"
            ))
            return TriageResult(
                ticket_id=ticket.id,
                urgency=UrgencyLevel.MEDIUM,
                product="Web & Client Application UI",
                issue_type="Software Defect / UI Glitch",
                customer_sentiment=SentimentLevel.NEUTRAL,
                summary=f"User reporting repeatable UI defect: '{ticket.messages[-1].content[:100]}'",
                next_action=NextActionType.ROUTE_TO_SPECIALIST,
                target_team_or_tier="Tier-2 Technical Support / Engineering Bug Triage",
                justification="Functional UI defect impacting workflow but not causing total system outage.",
                recommended_response="Acknowledge issue, gather client browser version/logs, and route reproduction steps to Engineering.",
                tools_used=tool_logs
            )
        # Low / FAQ / Feature Request
        else:
            query = "general inquiry how to settings feature request"
            kb_res = search_knowledge_base(query)
            tool_logs.append(ToolCallLog(
                tool_name="search_knowledge_base",
                arguments={"query": query},
                result_summary=f"Matched {kb_res.get('match_count')} articles"
            ))
            return TriageResult(
                ticket_id=ticket.id,
                urgency=UrgencyLevel.LOW,
                product="Customer Help Center & Platform Features",
                issue_type="General Inquiry / Feature Request",
                customer_sentiment=SentimentLevel.POSITIVE,
                summary=f"Informational inquiry or product enhancement request: '{ticket.messages[-1].content[:100]}'",
                next_action=NextActionType.AUTO_RESPOND,
                target_team_or_tier="Frontline Support / Product Feedback Backlog",
                justification="Self-service inquiry, setup guidance, or non-blocking feature request with standard documentation available.",
                recommended_response="Provide direct help-center documentation steps or confirm logging the request into the Product Backlog.",
                tools_used=tool_logs
            )

    def process_ticket(self, ticket: TicketInput) -> TriageResult:
        # Pre-Flight Input Guardrail: Detect Prompt Injection or Spam
        combined_text = " ".join([m.content for m in ticket.messages])
        is_flagged, guard_reason = check_input_guardrail(combined_text)

        if is_flagged:
            return TriageResult(
                ticket_id=ticket.id,
                urgency=UrgencyLevel.LOW,
                product="Security & Compliance Filter",
                issue_type="Security / Prompt Injection or Invalid Content",
                customer_sentiment=SentimentLevel.NEUTRAL,
                summary="System security guardrail flagged message for prompt injection or invalid/spam content.",
                next_action=NextActionType.ESCALATE_TO_HUMAN,
                target_team_or_tier="Security Operations / Trust & Safety",
                justification=f"Automated pre-flight block: {guard_reason}",
                recommended_response="This request has been blocked and routed to Security/Trust & Safety for manual inspection.",
                tools_used=[],
                is_flagged_by_guardrail=True,
                guardrail_notes=guard_reason
            )

        if not self.client:
            res = self._execute_mock_fallback(ticket)
            # Post-Flight Output Guardrail on mock
            out_flagged, out_reason = check_output_guardrail(res.recommended_response)
            if out_flagged:
                res.is_flagged_by_guardrail = True
                res.guardrail_notes = out_reason
            return res

        tool_logs: List[ToolCallLog] = []

        # Format conversation messages for LLM context
        thread_transcript = f"Customer Info: {ticket.customer_info}\nCustomer ID: {ticket.customer_id}\n\nMessage History:\n"
        for i, msg in enumerate(ticket.messages, 1):
            thread_transcript += f"[{msg.time_offset}] Message {i}: {msg.content}\n"

        messages = [
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Please analyze and triage Ticket {ticket.id}:\n\n{thread_transcript}"}
        ]

        # First pass: Tool calling loop (max 4 turns)
        for _ in range(4):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto"
            )
            resp_msg = response.choices[0].message
            messages.append(resp_msg)

            if not resp_msg.tool_calls:
                break

            for tc in resp_msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                tool_fn = TOOL_REGISTRY.get(fn_name)
                
                if tool_fn:
                    tool_output = tool_fn(**fn_args)
                else:
                    tool_output = {"error": f"Tool {fn_name} not found"}

                tool_logs.append(ToolCallLog(
                    tool_name=fn_name,
                    arguments=fn_args,
                    result_summary=f"Status: {tool_output.get('status', 'done')}"
                ))

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_output)
                })

        # Final pass: Enforce Structured Output according to TriageResult Pydantic schema
        structured_response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=TriageResult
        )

        final_result = structured_response.choices[0].message.parsed
        final_result.tools_used = tool_logs

        # Post-Flight Output Guardrail: Detect financial/legal promise hallucinations
        out_flagged, out_reason = check_output_guardrail(final_result.recommended_response)
        if out_flagged:
            final_result.is_flagged_by_guardrail = True
            final_result.guardrail_notes = out_reason

        return final_result
