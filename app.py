from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for all routes

# Database configuration
DB_NAME = 'data/registrations.db'

# Email configuration
EMAIL_TO = 'hongbin1016@icloud.com'

SECRET ='goqc-ygzu-mdom-cqwc'

def send_email(subject, html_content):
    """Send email with registration data"""
    try:
        # Email configuration - using local SMTP or you can configure your own
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_TO
        msg['To'] = EMAIL_TO
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email using local SMTP (you may need to configure this)
        # For production, use proper SMTP server with authentication
        try:
            with smtplib.SMTP('smtp.mail.me.com', 587) as server:
                server.starttls()
                server.login(EMAIL_TO, SECRET)
                server.send_message(msg)
            print(f"✓ Email sent successfully to {EMAIL_TO}")
            return True
        except Exception as smtp_error:
            # If local SMTP fails, try alternative or log the error
            print(f"✗ Failed to send email: {str(smtp_error)}")
            print(f"To: {EMAIL_TO}")
            print(f"Subject: {subject}")
            return False
            
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False

def send_email_async(subject, html_content):
    """Send email asynchronously in a background thread"""
    def send_in_background():
        print(f"→ Starting async email send to {EMAIL_TO}...")
        send_email(subject, html_content)
    
    thread = threading.Thread(target=send_in_background, daemon=True)
    thread.start()
    print(f"→ Email task queued in background thread")

def format_registrations_as_html_table(registrations):
    """Format registration data as HTML table"""
    if not registrations:
        return "<p>No registrations found.</p>"
    
    html = """
    <html>
    <head>
        <style>
            h2 {{ color: #004B8D; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th {{ background-color: #004B8D; color: white; padding: 12px; text-align: left; border: 1px solid #ddd; }}
            td {{ padding: 10px; border: 1px solid #ddd; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #e0e0e0; }}
            .summary {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h2>AIXDB Registration Data</h2>
        <div class="summary">
            <strong>Total Registrations:</strong> {count}<br>
            <strong>Generated:</strong> {timestamp}
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Mobile</th>
                    <th>Email</th>
                    <th>Organization</th>
                    <th>Registration Time</th>
                </tr>
            </thead>
            <tbody>
    """.format(
        count=len(registrations),
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    for reg in registrations:
        html += f"""
                <tr>
                    <td>{reg[0]}</td>
                    <td>{reg[1]}</td>
                    <td>{reg[2]}</td>
                    <td>{reg[3]}</td>
                    <td>{reg[4]}</td>
                    <td>{reg[5]}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    return html

def init_db():
    """Initialize the database and create tables if they don't exist"""
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            email TEXT NOT NULL,
            affiliation TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/api/register', methods=['POST', 'GET'])
def register():
    """Handle registration submissions and queries"""
    
    if request.method == 'GET':
        # GET method: retrieve all registrations and send email
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, mobile, email, affiliation, created_at
                FROM registrations
                ORDER BY created_at DESC
            ''')
            
            registrations = cursor.fetchall()
            conn.close()
            
            # Format as HTML table
            html_content = format_registrations_as_html_table(registrations)
            
            # Send email
            email_sent = send_email('AIXDB Registration Data', html_content)
            
            return jsonify({
                'success': True,
                'message': f'Found {len(registrations)} registrations. Email {"sent" if email_sent else "logged (SMTP not configured)"}.',
                'count': len(registrations),
                'email_sent': email_sent,
                'data': [{
                    'id': r[0],
                    'name': r[1],
                    'mobile': r[2],
                    'email': r[3],
                    'affiliation': r[4],
                    'created_at': r[5]
                } for r in registrations]
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    # POST method: create new registration
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['name', 'mobile', 'email', 'affiliation']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'message': f'Missing required field: {field}'
                    }), 400
            
            # Insert into database
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO registrations (name, mobile, email, affiliation)
                VALUES (?, ?, ?, ?)
            ''', (data['name'], data['mobile'], data['email'], data['affiliation']))
            
            conn.commit()
            registration_id = cursor.lastrowid
            
            # Get all registrations for email
            cursor.execute('''
                SELECT id, name, mobile, email, affiliation, created_at
                FROM registrations
                ORDER BY created_at DESC
            ''')
            registrations = cursor.fetchall()
            conn.close()
            
            # Send email asynchronously (non-blocking)
            html_content = format_registrations_as_html_table(registrations)
            send_email_async('AIXDB New Registration - Updated List', html_content)
            
            return jsonify({
                'success': True,
                'message': 'Registration successful!',
                'id': registration_id
            }), 201
            
        except Exception as e:
            print(e)
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'aixdb.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("Backend server starting...")
    print(f"Database: {DB_NAME}")
    print("Server URL: http://0.0.0.0:5000")
    print("API Endpoints:")
    print("  GET  /                 - Main page")
    print("  POST /api/register     - Submit registration")
    print("  GET  /api/register     - Get all registrations and send email")
    print("  GET  /api/health       - Health check")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
