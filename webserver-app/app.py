import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import base64
import datetime
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def main_page():
    return render_template('main.html', title="Home")

@app.route('/stats')
def stats_page():
    files = [
        datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(UPLOAD_FOLDER, f)))
        for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.jpeg')
    ]
    now = datetime.datetime.now()

    # Calculate hourly stats for all-time
    hourly_stats_all_time = [0] * 24
    for file_time in files:
        hourly_stats_all_time[file_time.hour] += 1

    # Calculate weekly stats for all-time
    weekly_stats_all_time = [0] * 7  # Monday = 0, Sunday = 6
    for file_time in files:
        weekly_stats_all_time[file_time.weekday()] += 1

    # Filter files for the past day
    past_day_files = [f for f in files if (now - f).days == 0]
    hourly_stats_past_day = [0] * 24
    for file_time in past_day_files:
        hourly_stats_past_day[file_time.hour] += 1

    # Filter files for the past week
    past_week_files = [f for f in files if (now - f).days < 7]
    daily_stats_past_week = [0] * 7  # Monday = 0, Sunday = 6
    for file_time in past_week_files:
        daily_stats_past_week[file_time.weekday()] += 1

    return render_template(
        'stats.html', 
        title="Stats",
        hourly_stats_all_time=hourly_stats_all_time,
        weekly_stats_all_time=weekly_stats_all_time,
        hourly_stats_past_day=hourly_stats_past_day,
        daily_stats_past_week=daily_stats_past_week
    ) 

@app.route('/history')
def history_page():
    '''for i in os.listdir("./static/uploads/"):
        print(i)
    jpeg_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.jpeg')]
    return render_template('history.html', title="History", jpeg_files=jpeg_files)'''
    files = [
        {
            'name': f,
            'timestamp': datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(UPLOAD_FOLDER, f))).strftime("%Y-%m-%d %H:%M:%S")
        }
        for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.jpeg')
    ]
    # Sort by modification time (newest first)
    files = sorted(files, key=lambda x: x['timestamp'], reverse=True)
    return render_template('history.html', title="History", files=files)


@app.route('/upload', methods=['POST'])
def upload_file():
    data = request.get_json()

    if not data or 'image' not in data:
        return jsonify({"error": "No image part in the request"}), 400

    # Decode the base64-encoded image data
    try:
        image_data = base64.b64decode(data['image'])

        # Get current time and generate unique identifier
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
        unique_id = uuid.uuid4().hex  # Generate a unique 32-character hex string

        file_name = f"image_{current_time}_{unique_id}.jpeg"
        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        # Save the decoded image data to a file
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        file_path = os.path.join(UPLOAD_FOLDER+"/current", "now.jpeg")

        # Save the decoded image data to a file
        with open(file_path, 'wb') as f:
            f.write(image_data)

        return jsonify({"message": "File uploaded successfully!"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to decode and save image: {e}"}), 500

@app.route('/upload_gif', methods=['POST'])
def upload_gif():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Get current time and generate a unique identifier for the file
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
    unique_id = uuid.uuid4().hex  # Generate a unique 32-character hex string
    
    # Save the uploaded file with a unique name
    file_name = f"file_{current_time}_{unique_id}.gif"
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    
    # Save the file to the server
    file.save(file_path)

    return jsonify({"message": "File uploaded successfully!", "file_name": file_name}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0",port="5000",debug=True)
