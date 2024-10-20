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
       
    return render_template('stats.html', title="Stats")

@app.route('/history')
def history_page():
    for i in os.listdir("./static/uploads/"):
        print(i)
    jpeg_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.jpeg')]
    return render_template('history.html', title="History", jpeg_files=jpeg_files)


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
