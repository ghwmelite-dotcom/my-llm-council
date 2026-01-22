"""Export conversations to Markdown format."""

from typing import Dict, Any, List
from datetime import datetime


def export_to_markdown(conversation: Dict[str, Any]) -> str:
    """
    Export a conversation to Markdown format.

    Args:
        conversation: The conversation dict with messages

    Returns:
        Markdown string
    """
    lines = []

    # Header
    title = conversation.get('title', 'Untitled Conversation')
    created_at = conversation.get('created_at', '')
    conv_id = conversation.get('id', '')

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Conversation ID:** `{conv_id}`")
    lines.append(f"**Created:** {created_at}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Messages
    messages = conversation.get('messages', [])

    for i, msg in enumerate(messages):
        if msg.get('role') == 'user':
            lines.append("## User Query")
            lines.append("")
            lines.append(msg.get('content', ''))
            lines.append("")

        elif msg.get('role') == 'assistant':
            lines.append("## Council Response")
            lines.append("")

            # Stage 1: Individual Responses
            stage1 = msg.get('stage1', [])
            if stage1:
                lines.append("### Stage 1: Individual Model Responses")
                lines.append("")
                for response in stage1:
                    model = response.get('model', 'Unknown')
                    model_name = model.split('/')[-1] if '/' in model else model
                    content = response.get('response', '')
                    lines.append(f"#### {model_name}")
                    lines.append("")
                    lines.append(content)
                    lines.append("")

            # Stage 2: Peer Rankings
            stage2 = msg.get('stage2', [])
            if stage2:
                lines.append("### Stage 2: Peer Rankings")
                lines.append("")

                # Show aggregate rankings if available
                metadata = msg.get('metadata', {})
                aggregate = metadata.get('aggregate_rankings', [])
                if aggregate:
                    lines.append("#### Aggregate Rankings")
                    lines.append("")
                    lines.append("| Rank | Model | Avg Position |")
                    lines.append("|------|-------|--------------|")
                    for rank, item in enumerate(aggregate, 1):
                        model = item.get('model', 'Unknown')
                        model_name = model.split('/')[-1] if '/' in model else model
                        avg_rank = item.get('average_rank', 0)
                        lines.append(f"| {rank} | {model_name} | {avg_rank:.2f} |")
                    lines.append("")

                # Individual rankings
                for ranking in stage2:
                    model = ranking.get('model', 'Unknown')
                    model_name = model.split('/')[-1] if '/' in model else model
                    ranking_text = ranking.get('ranking', '')
                    lines.append(f"<details>")
                    lines.append(f"<summary><strong>{model_name}'s Evaluation</strong></summary>")
                    lines.append("")
                    lines.append(ranking_text)
                    lines.append("")
                    lines.append("</details>")
                    lines.append("")

            # Stage 3: Final Answer
            stage3 = msg.get('stage3', {})
            if stage3:
                lines.append("### Stage 3: Final Council Answer")
                lines.append("")
                chairman = stage3.get('model', 'Unknown')
                chairman_name = chairman.split('/')[-1] if '/' in chairman else chairman
                response = stage3.get('response', '')
                lines.append(f"**Chairman:** {chairman_name}")
                lines.append("")
                lines.append(response)
                lines.append("")

            # Cost summary if available
            cost = msg.get('costSummary', {})
            if cost:
                lines.append("### Cost Summary")
                lines.append("")
                lines.append(f"- **Total Cost:** {cost.get('total_cost_formatted', 'N/A')}")
                lines.append(f"- **Total Tokens:** {cost.get('total_tokens', 0):,}")
                lines.append(f"- **API Calls:** {cost.get('api_calls', 0)}")
                lines.append("")

        lines.append("---")
        lines.append("")

    # Footer
    lines.append(f"*Exported from LLM Council on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*")

    return "\n".join(lines)


def get_markdown_filename(conversation: Dict[str, Any]) -> str:
    """Generate a filename for the markdown export."""
    title = conversation.get('title', 'conversation')
    # Sanitize title for filename
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
    safe_title = safe_title.strip().replace(' ', '_')[:50]
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f"{safe_title}_{timestamp}.md"
