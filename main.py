from process_detect import processDetect
from flask import Flask, request
import os
import uuid
from pydub import AudioSegment
from werkzeug.utils import secure_filename


app=Flask(__name__)

# ROUTING
@app.route('/')
def index():
    return '<h1>Hello world</h1>'

@app.route('/detected-species', methods=['POST'])
def Detected_species():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        UPLOAD_FOLDER = r'E:\KERJA\spudniklab\InsectoscopeProjectApiLokalDisk\upload'
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        filename = secure_filename(file.filename)  # Secure filename

        # Check MIME type
        mime_type = file.content_type
        if mime_type != 'audio/wav':
            # Convert to WAV before saving
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            audio = AudioSegment.from_file(temp_path)
            unique_filename = str(uuid.uuid4()) + '.wav'
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            audio.export(file_path, format='wav')
            os.remove(temp_path)  # Remove the original file
        else:
            unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]  # Generate unique filename with original file extension
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

        file_info = {'filename': unique_filename, 'filetype': 'audio/wav'}
        result = processDetect(unique_filename)
        # Delete the file after processing
        try:
            os.remove(file_path)
        except Exception as e:
            return {'error': f'File deletion failed: {e}'}, 500

        return result



if __name__ == "__main__":
    app.run()