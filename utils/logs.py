"""Logs view and utilities."""
from django.http import HttpResponse
from config import ENABLE_LOGS
from utils.logging import get_log_buffer


def render_logs():
    """Render logs page."""
    if not ENABLE_LOGS:
        return HttpResponse("Logs service not enabled. Set LOGS=true to enable.", status=404)
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Proxy Logs</title>
  <style>
    body {
      font-family: 'Courier New', monospace;
      background: #1e1e1e;
      color: #d4d4d4;
      margin: 0;
      padding: 20px;
    }
    h1 {
      color: #4ec9b0;
      font-size: 1.5em;
    }
    .log-container {
      background: #252526;
      padding: 20px;
      border-radius: 8px;
      overflow-x: auto;
    }
    .log-line {
      padding: 4px 0;
      border-bottom: 1px solid #333;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .log-line:hover {
      background: #2d2d30;
    }
    .timestamp {
      color: #858585;
    }
    .proxy { color: #4ec9b0; }
    .rewrite { color: #dcdcaa; }
    .error { color: #f48771; }
    .warning { color: #ce9178; }
    .refresh {
      display: inline-block;
      margin: 10px 0;
      padding: 8px 16px;
      background: #0e639c;
      color: white;
      text-decoration: none;
      border-radius: 4px;
    }
    .refresh:hover {
      background: #1177bb;
    }
  </style>
</head>
<body>
  <h1>📋 Proxy Logs (Last 1000 lines)</h1>
  <a href="/_logs/" class="refresh">🔄 Refresh</a>
  <a href="/" class="refresh">← Home</a>
  <div class="log-container">
"""
    
    log_buffer = get_log_buffer()
    if not log_buffer:
        html += '<div class="log-line">No logs yet...</div>'
    else:
        for line in log_buffer:
            css_class = ""
            if "[PROXY]" in line:
                css_class = "proxy"
            elif "[REWRITE]" in line:
                css_class = "rewrite"
            elif "[ERROR]" in line:
                css_class = "error"
            elif "[WARNING]" in line:
                css_class = "warning"
            
            html += f'<div class="log-line {css_class}">{line}</div>\n'
    
    html += """
  </div>
</body>
</html>
"""
    
    return HttpResponse(html)
