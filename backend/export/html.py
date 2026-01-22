"""Export conversations to HTML format (for PDF printing)."""

from typing import Dict, Any
from datetime import datetime
import html


def export_to_html(conversation: Dict[str, Any]) -> str:
    """
    Export a conversation to HTML format suitable for PDF printing.

    Args:
        conversation: The conversation dict with messages

    Returns:
        HTML string
    """
    title = html.escape(conversation.get('title', 'Untitled Conversation'))
    created_at = conversation.get('created_at', '')
    conv_id = conversation.get('id', '')

    # Build HTML content
    content_parts = []

    messages = conversation.get('messages', [])
    for msg in messages:
        if msg.get('role') == 'user':
            user_content = html.escape(msg.get('content', ''))
            content_parts.append(f'''
            <div class="message user-message">
                <h2>User Query</h2>
                <div class="content">{user_content}</div>
            </div>
            ''')

        elif msg.get('role') == 'assistant':
            # Stage 1
            stage1 = msg.get('stage1', [])
            if stage1:
                stage1_html = '<div class="stage stage1"><h3>Stage 1: Individual Model Responses</h3>'
                for response in stage1:
                    model = response.get('model', 'Unknown')
                    model_name = model.split('/')[-1] if '/' in model else model
                    resp_content = html.escape(response.get('response', ''))
                    stage1_html += f'''
                    <div class="model-response">
                        <h4>{html.escape(model_name)}</h4>
                        <div class="response-content">{resp_content}</div>
                    </div>
                    '''
                stage1_html += '</div>'
                content_parts.append(stage1_html)

            # Stage 2
            stage2 = msg.get('stage2', [])
            metadata = msg.get('metadata', {})
            aggregate = metadata.get('aggregate_rankings', [])

            if stage2 or aggregate:
                stage2_html = '<div class="stage stage2"><h3>Stage 2: Peer Rankings</h3>'

                if aggregate:
                    stage2_html += '<div class="aggregate-rankings"><h4>Aggregate Rankings</h4><table>'
                    stage2_html += '<tr><th>Rank</th><th>Model</th><th>Avg Position</th></tr>'
                    for rank, item in enumerate(aggregate, 1):
                        model = item.get('model', 'Unknown')
                        model_name = model.split('/')[-1] if '/' in model else model
                        avg_rank = item.get('average_rank', 0)
                        stage2_html += f'<tr><td>{rank}</td><td>{html.escape(model_name)}</td><td>{avg_rank:.2f}</td></tr>'
                    stage2_html += '</table></div>'

                stage2_html += '</div>'
                content_parts.append(stage2_html)

            # Stage 3
            stage3 = msg.get('stage3', {})
            if stage3:
                chairman = stage3.get('model', 'Unknown')
                chairman_name = chairman.split('/')[-1] if '/' in chairman else chairman
                final_response = html.escape(stage3.get('response', ''))
                content_parts.append(f'''
                <div class="stage stage3">
                    <h3>Stage 3: Final Council Answer</h3>
                    <div class="chairman-label">Chairman: {html.escape(chairman_name)}</div>
                    <div class="final-response">{final_response}</div>
                </div>
                ''')

            # Cost
            cost = msg.get('costSummary', {})
            if cost:
                content_parts.append(f'''
                <div class="cost-summary">
                    <h4>Cost Summary</h4>
                    <p><strong>Total Cost:</strong> {html.escape(str(cost.get('total_cost_formatted', 'N/A')))}</p>
                    <p><strong>Total Tokens:</strong> {cost.get('total_tokens', 0):,}</p>
                    <p><strong>API Calls:</strong> {cost.get('api_calls', 0)}</p>
                </div>
                ''')

    content = "\n".join(content_parts)
    export_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - LLM Council</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #333;
            background: #fff;
        }}
        h1 {{
            color: #1a1a2e;
            border-bottom: 3px solid #4a90e2;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #16213e;
            margin-top: 30px;
        }}
        h3 {{
            color: #0f3460;
            margin-top: 25px;
        }}
        h4 {{
            color: #4a90e2;
            margin-top: 15px;
        }}
        .meta {{
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
        }}
        .message {{
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
        }}
        .user-message {{
            background: #f0f4f8;
            border-left: 4px solid #4a90e2;
        }}
        .stage {{
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
        }}
        .stage1 {{
            background: #fff8f0;
            border-left: 4px solid #f59e0b;
        }}
        .stage2 {{
            background: #f0f8ff;
            border-left: 4px solid #3b82f6;
        }}
        .stage3 {{
            background: #f0fff4;
            border-left: 4px solid #22c55e;
        }}
        .model-response {{
            margin: 15px 0;
            padding: 15px;
            background: rgba(255,255,255,0.7);
            border-radius: 6px;
        }}
        .response-content, .final-response {{
            white-space: pre-wrap;
            font-size: 14px;
        }}
        .chairman-label {{
            color: #22c55e;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #f5f5f5;
        }}
        .cost-summary {{
            margin: 20px 0;
            padding: 15px;
            background: #fef3c7;
            border-radius: 8px;
            border-left: 4px solid #f59e0b;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
            text-align: center;
        }}
        @media print {{
            body {{
                padding: 20px;
            }}
            .stage, .message {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="meta">
        <p><strong>Conversation ID:</strong> <code>{html.escape(conv_id)}</code></p>
        <p><strong>Created:</strong> {html.escape(created_at)}</p>
    </div>

    {content}

    <div class="footer">
        Exported from LLM Council on {export_time} UTC
    </div>
</body>
</html>'''


def get_html_filename(conversation: Dict[str, Any]) -> str:
    """Generate a filename for the HTML export."""
    title = conversation.get('title', 'conversation')
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
    safe_title = safe_title.strip().replace(' ', '_')[:50]
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f"{safe_title}_{timestamp}.html"
