import argparse
import json
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows console compatibility
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.models import TicketInput, TriageResult
from src.agent import SupportTriageAgent
from src.config import OPENAI_API_KEY, OPENAI_MODEL

console = Console()

def load_sample_tickets() -> list[TicketInput]:
    data_file = Path(__file__).resolve().parent / "data" / "sample_tickets.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [TicketInput(**t) for t in data["tickets"]]

def display_triage_result(res: TriageResult):
    urgency_color = {
        "critical": "bold red",
        "high": "bold orange3",
        "medium": "bold yellow",
        "low": "bold green"
    }.get(res.urgency.value, "white")

    table = Table(title=f"Triage Decision Report: {res.ticket_id}", show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan", width=22)
    table.add_column("Assessment / Value", style="white")

    table.add_row("Urgency", f"[{urgency_color}]{res.urgency.value.upper()}[/{urgency_color}]")
    table.add_row("Product Area", res.product)
    table.add_row("Issue Type", res.issue_type)
    table.add_row("Customer Sentiment", res.customer_sentiment.value)
    table.add_row("Next Action", f"[bold underline]{res.next_action.value.upper()}[/bold underline]")
    table.add_row("Assigned Tier / Team", res.target_team_or_tier or "N/A")
    table.add_row("Summary", res.summary)
    table.add_row("Decision Justification", res.justification)
    table.add_row("Recommended Response", res.recommended_response)

    console.print(table)

    if res.tools_used:
        tool_table = Table(title=f"Tools Invoked for {res.ticket_id}", show_header=True, header_style="bold blue")
        tool_table.add_column("Tool Name", style="green")
        tool_table.add_column("Arguments", style="dim")
        tool_table.add_column("Result Summary", style="yellow")
        for t in res.tools_used:
            tool_table.add_row(t.tool_name, json.dumps(t.arguments), t.result_summary)
        console.print(tool_table)
    console.print("\n" + "="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(description="AI Support Ticket Triage Agent Runner")
    parser.add_argument("--ticket", type=str, choices=["TICKET-001", "TICKET-002", "TICKET-003", "ALL"], default="ALL",
                        help="Select specific ticket ID to run or ALL (default)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of tables")
    args = parser.parse_args()

    tickets = load_sample_tickets()
    if args.ticket != "ALL":
        tickets = [t for t in tickets if t.id == args.ticket]

    mode_info = f"Using OpenAI Model: [bold green]{OPENAI_MODEL}[/bold green]" if OPENAI_API_KEY else "[bold yellow]Running in Mock Fallback Mode (No OPENAI_API_KEY detected in .env)[/bold yellow]"
    console.print(Panel(mode_info, title="[bold]Support Ticket Triage System[/bold]", expand=False))

    agent = SupportTriageAgent()
    results = []

    for ticket in tickets:
        res = agent.process_ticket(ticket)
        results.append(res)
        if not args.json:
            display_triage_result(res)

    if args.json:
        print(json.dumps([r.model_dump() for r in results], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
