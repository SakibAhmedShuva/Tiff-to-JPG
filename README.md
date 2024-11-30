# TIFF to JPG Converter API

A Flask-based REST API service that converts TIFF images to JPG format with optimization for efficient storage and transfer. The service includes both single file and batch conversion capabilities, with built-in safety features and size limitations.

## Features

- Single TIFF to JPG conversion
- Batch conversion support (up to 150 files)
- Automatic image resizing and optimization
- File size limits and safety checks
- Detailed logging
- Health check endpoint
- Error handling and validation
- Secure filename handling

## Requirements

- Python 3.x
- Flask 3.1.0
- Pillow 11.0.0
- Werkzeug 3.1.3

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SakibAhmedShuva/Tiff-to-JPG-Converter.git
cd Tiff-to-JPG-Converter
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The following configuration parameters can be adjusted in `tiff2jpg.py`:

```python
MAX_IMAGE_SIZE = 2000000000  # Maximum pixel limit
MAX_INPUT_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB input file size limit
MAX_OUTPUT_FILE_SIZE = 10 * 1024 * 1024  # 10MB output file size limit
ALLOWED_EXTENSIONS = {'tif', 'tiff'}
```

## Usage

### Starting the Server

Run the Flask application:
```bash
python tiff2jpg.py
```

The server will start on `http://localhost:5000` by default.

### API Endpoints

#### 1. Health Check
```http
GET /health
```
Returns the service status and configuration details.

#### 2. Single File Conversion
```http
POST /convert
```
Convert a single TIFF file to JPG format.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (TIFF file)

**Example using curl:**
```bash
curl -X POST -F "file=@image.tiff" http://localhost:5000/convert -O -J
```

#### 3. Batch Conversion
```http
POST /batch-convert
```
Convert multiple TIFF files to JPG format.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: files[] (Array of TIFF files)

**Example using curl:**
```bash
curl -X POST -F "files[]=@image1.tiff" -F "files[]=@image2.tiff" http://localhost:5000/batch-convert
```

### Response Formats

#### Single File Conversion
- Success: Returns the converted JPG file
- Error: Returns JSON with error details
```json
{
    "error": "Error message"
}
```

#### Batch Conversion
Returns JSON with conversion results:
```json
{
    "successful_conversions": [
        {
            "filename": "image1.tiff",
            "output_path": "converted/image1.jpg",
            "output_size_mb": 2.5
        }
    ],
    "failed_conversions": [
        {
            "filename": "image2.tiff",
            "reason": "File size exceeds limit"
        }
    ]
}
```

## Limitations and Safety Features

- Maximum input file size: 1GB
- Maximum output file size: 10MB
- Maximum batch size: 150 files
- Supported input formats: .tif, .tiff
- Output format: .jpg
- Maximum output image dimensions: 2800x2800 pixels
- JPEG quality: 80% (optimized)

## Error Handling

The API includes comprehensive error handling for:
- Missing files
- Invalid file types
- File size violations
- Processing errors
- Conversion failures

## Logging

The application logs all operations with timestamps and details to help with monitoring and debugging. Logs include:
- Request information
- Processing status
- Error details
- File operations

## Development

The project structure is organized as follows:
```
Tiff-to-JPG-Converter/
├── tiff2jpg.py
├── requirements.txt
├── uploads/           # Temporary storage for uploads
└── converted/         # Output directory for converted files
```

## License

This project is open source and available under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For support, please open an issue in the GitHub repository.
