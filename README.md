# Point Cloud Analysis Agent

An AI-powered application for analyzing LiDAR point cloud data using LangChain agents and Open3D for 3D mesh reconstruction.

## Features

### Core Analysis
- **AI-Powered Analysis**: Uses LangChain agents with Google's Gemini model for intelligent point cloud processing
- **3D Mesh Reconstruction**: Creates 3D meshes from point cloud data using Open3D
- **RANSAC Plane Segmentation**: Advanced algorithm for ground and wall detection
- **Configurable Parameters**: Customizable analysis parameters for different use cases

### Visualization & Interaction
- **3D Point Cloud Visualization**: Interactive 3D viewing with color-coded classifications
- **Interactive 2D Cross-Sections**: Measure distances and analyze tunnel profiles
- **Profile Comparison**: Compare actual vs. design profiles
- **Alpha Shape Profiles**: Generate actual tunnel profiles using computational geometry

### AI & Reporting
- **AI Report Generation**: Automated technical reports using Google Generative AI
- **Cross-Section Analysis**: AI-powered analysis of tunnel cross-sections
- **Export Capabilities**: Export data to CSV and 3D mesh formats

### User Interface
- **Modern GUI**: Professional Tkinter-based interface with dark theme support
- **Smart File Handling**: Automatic file validation and dialog-based file selection
- **Progress Tracking**: Real-time progress indicators and status updates
- **Comprehensive Menus**: Organized menu system for all features

### File Support
- **LAS/LAZ Support**: Full support for both compressed and uncompressed LAS files
- **File Validation**: Comprehensive validation with helpful error messages
- **Profile Import**: Import design profiles from CSV files
- **Data Export**: Export analysis results in multiple formats

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd point-cloud-analysis-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

1. **Load a LAS file**: Use the "Browse" button to select a .las or .laz file
2. **Set objective**: Enter your analysis objective (or use the default)
3. **Start analysis**: Click "Start Analysis" to begin processing
4. **View results**: Monitor the AI agent's progress in the output window

### File Handling

The application includes smart file handling features:

- **File Validation**: Automatically validates LAS/LAZ files before processing
- **File Dialog**: If a file is not found, a dialog will appear to select the correct file
- **File Information**: Shows file size and path information in the output
- **Error Messages**: Clear error messages for common file issues

### Supported File Formats

- `.las` - Standard LAS format
- `.laz` - Compressed LAS format

## Configuration

The application can be configured through environment variables:

- `MODEL_NAME`: AI model to use (default: "models/gemini-pro-latest")
- `TEMPERATURE`: Model temperature (default: 0.0)
- `LOG_LEVEL`: Logging level (default: "INFO")

## Project Structure

```
├── agent/                 # AI agent modules
│   ├── __init__.py
│   └── agent_core.py
├── analysis/              # Point cloud analysis modules
│   ├── __init__.py
│   └── point_cloud_processor.py
├── gui/                   # GUI modules
│   ├── __init__.py
│   └── main_window.py
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── exceptions.py
│   └── logger.py
├── config.py              # Configuration management
├── main.py               # Main application entry point
├── requirements.txt      # Python dependencies
└── setup.py             # Package setup script
```

## Dependencies

- **numpy**: Numerical computing
- **laspy**: LAS file reading
- **open3d**: 3D data processing and visualization
- **langchain**: AI agent framework
- **langchain-google-genai**: Google Gemini integration
- **tkinter**: GUI framework
- **sv-ttk**: Modern Tkinter theme

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please open an issue on the GitHub repository.
