"""
Alerting Module
Sends alerts to Slack for critical events
"""

import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')


def send_alert(message: str, severity: str = 'warning'):
    """
    Send an alert message to Slack.
    
    Args:
        message: Alert message
        severity: Alert severity ('info', 'warning', 'error', 'critical')
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not configured, alert not sent")
        logger.warning(f"[{severity.upper()}] {message}")
        return
    
    # Color coding by severity
    colors = {
        'info': '#36a64f',      # Green
        'warning': '#ff9900',   # Orange
        'error': '#ff0000',     # Red
        'critical': '#8b0000'   # Dark red
    }
    
    # Emoji by severity
    emojis = {
        'info': ':information_source:',
        'warning': ':warning:',
        'error': ':x:',
        'critical': ':rotating_light:'
    }
    
    payload = {
        'attachments': [{
            'color': colors.get(severity, '#808080'),
            'title': f"{emojis.get(severity, '')} Stablecoin Analytics Alert",
            'text': message,
            'footer': 'Stablecoin Analytics Platform',
            'ts': int(datetime.utcnow().timestamp())
        }]
    }
    
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.debug(f"Alert sent to Slack: {message}")
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {str(e)}")
