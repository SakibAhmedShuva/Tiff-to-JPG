from flask import Flask, request, send_file
from PIL import Image
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import io
import zipfile

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Configure settings
MAX_IMAGE_SIZE = 2000000000  # Increased pixel limit
Image.MAX_IMAGE_PIXELS = None  # Disable Pillow's decompression bomb protection for larger images
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'converted'
ALLOWED_EXTENSIONS = {'tif', 'tiff'}
MAX_INPUT_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB input file size limit
MAX_OUTPUT_FILE_SIZE = 10 * 1024 * 1024   # 10MB output file size limit

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_file_size(file):
    """Check if file size is within limits"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)  # Reset file pointer
    return size <= MAX_INPUT_FILE_SIZE

def convert_tif_to_jpg(input_path, output_path, max_size=(2800, 2800)):
    """Convert TIF image to JPG format with low resolution"""
    try:
        with Image.open(input_path) as img:
            # Resize the image if it exceeds the maximum size
            if max(img.size) > max(max_size):
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            img.save(output_path, 'JPEG', quality=80, optimize=True)
        logger.info(f"Conversion successful: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        return True
    except Exception as e:
        logger.error(f"Error converting {os.path.basename(input_path)}: {str(e)}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint to check if the API is running"""
    logger.info("Health check requested")
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'max_input_file_size_mb': MAX_INPUT_FILE_SIZE / (1024 * 1024),
        'max_output_file_size_mb': MAX_OUTPUT_FILE_SIZE / (1024 * 1024),
        'max_image_pixels': "unlimited" if Image.MAX_IMAGE_PIXELS is None else Image.MAX_IMAGE_PIXELS
    }

@app.route('/convert', methods=['POST'])
def convert_image():
    """Endpoint to convert TIF images to JPG"""
    if 'file' not in request.files:
        logger.error("No file provided in request")
        return {'error': 'No file provided'}, 400

    file = request.files['file']

    if file.filename == '':
        logger.error("No file selected")
        return {'error': 'No file selected'}, 400

    logger.info(f"Received conversion request for file: {file.filename}")

    if not allowed_file(file.filename):
        logger.error(f"Invalid file type for: {file.filename}")
        return {'error': 'Invalid file type. Only TIF/TIFF files are allowed'}, 400

    if not check_file_size(file):
        logger.error(f"File size exceeds limit: {file.filename}")
        return {
            'error': f'File size exceeds maximum limit of {MAX_INPUT_FILE_SIZE / (1024 * 1024)}MB'
        }, 400

    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_filename = f"{filename.rsplit('.', 1)[0]}.jpg"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        logger.info(f"Starting conversion process for: {filename}")

        # Save uploaded file
        file.save(input_path)
        logger.info(f"File saved to: {input_path}")

        # Convert the image
        if convert_tif_to_jpg(input_path, output_path, max_size=(2800, 2800)):
            os.remove(input_path)
            logger.info(f"Removed input file: {input_path}")

            # Check final output size
            output_size = os.path.getsize(output_path)
            if output_size > MAX_OUTPUT_FILE_SIZE:
                os.remove(output_path)
                logger.error(f"Output file size ({output_size/(1024*1024):.1f}MB) exceeds limit")
                return {
                    'error': f'Output file size ({output_size/(1024*1024):.1f}MB) exceeds limit of {MAX_OUTPUT_FILE_SIZE/(1024*1024)}MB'
                }, 400

            logger.info(f"Conversion successful. Sending file: {output_filename}")
            return send_file(output_path, mimetype='image/jpeg', as_attachment=True,
                              download_name=output_filename)
        else:
            if os.path.exists(input_path):
                os.remove(input_path)
            logger.error(f"Conversion failed for: {filename}")
            return {'error': 'Conversion failed'}, 500

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        if os.path.exists(input_path):
            os.remove(input_path)
        return {'error': 'Internal server error'}, 500

@app.route('/batch-convert', methods=['POST'])
def batch_convert_images():
    """Endpoint to convert multiple TIF images to JPG"""
    if 'files[]' not in request.files:
        logger.error("No files provided in request")
        return {'error': 'No files provided'}, 400

    files = request.files.getlist('files[]')
    
    if not files or len(files) == 0:
        logger.error("No files selected")
        return {'error': 'No files selected'}, 400

    if len(files) > 150:  # Limit number of files in batch
        logger.error(f"Too many files: {len(files)}")
        return {'error': 'Maximum 150 files allowed per batch'}, 400

    logger.info(f"Received batch conversion request for {len(files)} files")

    response = {
        'successful_conversions': [],
        'failed_conversions': []
    }

    for file in files:
        if file.filename == '':
            response['failed_conversions'].append({
                'filename': 'Unnamed',
                'reason': 'File has no name'
            })
            continue

        if not allowed_file(file.filename):
            response['failed_conversions'].append({
                'filename': file.filename,
                'reason': 'Invalid file type'
            })
            continue

        if not check_file_size(file):
            response['failed_conversions'].append({
                'filename': file.filename,
                'reason': f'File size exceeds {MAX_INPUT_FILE_SIZE / (1024 * 1024)}MB limit'
            })
            continue

        try:
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            output_filename = f"{filename.rsplit('.', 1)[0]}.jpg"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            # Save uploaded file
            file.save(input_path)

            # Convert the image
            if convert_tif_to_jpg(input_path, output_path, max_size=(2800, 2800)):
                # Check output file size
                output_size = os.path.getsize(output_path)
                if output_size <= MAX_OUTPUT_FILE_SIZE:
                    response['successful_conversions'].append({
                        'filename': file.filename,
                        'output_path': output_path,
                        'output_size_mb': round(output_size / (1024 * 1024), 2)
                    })
                else:
                    os.remove(output_path)
                    response['failed_conversions'].append({
                        'filename': file.filename,
                        'reason': f'Output file size ({output_size/(1024*1024):.1f}MB) exceeds limit'
                    })

            else:
                response['failed_conversions'].append({
                    'filename': file.filename,
                    'reason': 'Conversion failed'
                })

            # Cleanup input file
            if os.path.exists(input_path):
                os.remove(input_path)

        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            response['failed_conversions'].append({
                'filename': file.filename,
                'reason': 'Processing error'
            })
            if os.path.exists(input_path):
                os.remove(input_path)

    # Return JSON response
    return response, 200 if response['successful_conversions'] else 400

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=True)
