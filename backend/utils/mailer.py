import urllib.request
import urllib.parse
import base64
from flask import current_app

def send_email(to, subject, text, html=None):
    """
    Sends an email using Mailgun API via urllib.request.
    """
    mailgun_url = current_app.config.get('MAILGUN_URL')
    mailgun_key = current_app.config.get('MAILGUN_KEY')
    from_address = current_app.config.get('MAILGUN_SEND_FROM_ADDRESS')

    if not all([mailgun_url, mailgun_key, from_address]):
        current_app.logger.warning("Mailgun configuration missing, skipping email sending.")
        # In development/test if not configured, we still want to know it was triggered
        if current_app.debug:
            current_app.logger.debug(f"DEBUG: Email would be sent to {to}")
            current_app.logger.debug(f"Subject: {subject}")
            current_app.logger.debug(f"Text: {text}")
        return False

    data = {
        'from': from_address,
        'to': to,
        'subject': subject,
        'text': text
    }
    if html:
        data['html'] = html

    payload = urllib.parse.urlencode(data).encode('utf-8')
    
    # Mailgun uses 'api' as the username for Basic Auth
    auth_str = f"api:{mailgun_key}"
    auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    
    req = urllib.request.Request(mailgun_url, data=payload, method='POST')
    req.add_header('Authorization', f'Basic {auth_b64}')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            if 200 <= status < 300:
                current_app.logger.info(f"Email sent to {to} successfully.")
                return True
            else:
                current_app.logger.error(f"Failed to send email to {to}. Status: {status}")
                return False
    except Exception as e:
        current_app.logger.error(f"Error sending email to {to}: {str(e)}")
        return False
