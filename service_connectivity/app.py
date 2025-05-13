import os
import requests
import logging
from flask import Flask, jsonify
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from shared.debugger_client import log_to_debugger, record_exchange

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


INTERNAL_SERVICES = [
    {'name': 'gateway', 'url': 'http://gateway:5000/health'},
    {'name': 'service_contacts', 'url': 'http://service_contacts:5000/health'},
    {'name': 'service_transform', 'url': 'http://service_transform:5000/health'},
    {'name': 'service_debugger', 'url': 'http://service_debugger:5000/health'},
    {'name': 'service_storage', 'url': 'http://service_storage:5000/health'},
    {'name': 'service_project', 'url': 'http://service_project:5000/health'},
]


@app.route('/check-dependencies', methods=['POST'])
def check_dependencies():
    """Check if all required services for a specific operation are available"""
    required_services = request.json.get('services', [])
    operation = request.json.get('operation', 'unknown')

    log_to_debugger("connectivity", "info", f"Checking dependencies for operation: {operation}", {
        "required_services": required_services
    })
    
    # Map short service names to full service names
    service_map = {
        'transform': 'service_transform',
        'storage': 'service_storage',
        'debugger': 'service_debugger',
        'contacts': 'service_contacts',
        'project': 'service_project'
    }
    
    results = {}
    all_available = True
    
    for service in required_services:
        service_name = service_map.get(service, service)
        logger.info(f"Checking service: {service} (mapped to {service_name})")
        
        # Find service in internal services list
        service_found = False
        for internal_service in INTERNAL_SERVICES:
            if internal_service['name'] == service_name:
                service_found = True
                service_url = internal_service['url']
                
                try:
                    logger.info(f"Testing URL: {service_url}")
                    response = requests.get(service_url, timeout=2)
                    available = response.status_code == 200
                    results[service] = {
                        'available': available,
                        'status_code': response.status_code
                    }
                    if not available:
                        all_available = False
                        logger.warning(f"Service {service_name} returned status code {response.status_code}")
                except Exception as e:
                    logger.error(f"Error checking service {service_name}: {str(e)}")
                    results[service] = {
                        'available': False,
                        'error': str(e)
                    }
                    all_available = False
                
                break
        
        if not service_found:
            log_to_debugger("connectivity", "warning", f"Service unavailable: {service_name}", {
                "status_code": response.status_code,
                "operation": operation
            })
            results[service] = {
                'available': False,
                'error': 'Service not found'
            }
            all_available = False
    
    # If some services are unavailable, send an email alert
    if not all_available:
        log_to_debugger("connectivity", "alert", "Services unavailable", {
            "operation": operation,
            "unavailable_services": unavailable_services
        })
        unavailable_services = [s for s, r in results.items() if not r['available']]
        
        subject = f"SERVICE ALERT: Services unavailable for {operation}"
        body = f"""
        <h2>Service Dependency Failure</h2>
        <p>The following services are unavailable for operation: <strong>{operation}</strong></p>
        <ul>
            {"".join([f"<li>{service}</li>" for service in unavailable_services])}
        </ul>
        <p>Please check the system immediately.</p>
        <hr>
        <p><i>This is an automated message from your microservices monitoring system.</i></p>
        """
        send_email_alert(subject, body)
    
    return jsonify({
        'operation': operation,
        'all_available': all_available,
        'services': results
    })

def send_email_alert(subject, message_body):
    """Send an email alert when services are unavailable"""
    try:
        # Get SMTP configuration from environment variables
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER', 'ahaloui@tm-holding.ma')
        smtp_password = os.environ.get('SMTP_PASSWORD', 'mdkj llqv agca dwxn')
        recipient = os.environ.get('ALERT_EMAIL', 'ahaloui@tm-holding.ma')
        
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(message_body, 'html'))
        
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable secure connection
        server.login(smtp_user, smtp_password)
        
        # Send the email
        server.send_message(msg)
        server.quit()
        
        log_to_debugger("connectivity", "info", "Email alert sent successfully")
        return True
    except Exception as e:
        log_to_debugger("connectivity", "error", f"Failed to send email alert: {str(e)}")
        return False


if __name__ == "__main__":
    log_to_debugger("connectivity", "info", "Connectivity service started")
    app.run(host="0.0.0.0", port=5000, debug=True)