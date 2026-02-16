# Research Paper Analyzer - Streamlit App

A web-based interface for analyzing research papers on supply chain management and AI.

## Features

- 📤 **Upload Multiple PDFs**: Upload one or multiple research papers at once
- 📖 **Automatic Parsing**: PDFs are automatically parsed and chunked for analysis
- 🤖 **AI-Powered Analysis**: Extract structured dimensions using Claude AI
- 📊 **View Results**: Browse analysis results in an organized interface
- 💾 **Export Options**: Download results in JSON, CSV, or Excel format

## Installation

1. Install dependencies:
```bash
pip install -r ../requirements.txt
```

2. Make sure you have your Anthropic API key in the `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Running the App

From the project root directory, run:
```bash
streamlit run app/main.py
```

Or from the `app` directory:
```bash
cd app
streamlit run main.py
```

The app will open in your default web browser at `http://localhost:8501`

## Usage

1. **Upload PDFs**: Use the file uploader in the "Upload & Process" tab to select one or more PDF files
2. **Process**: Click the "Process Papers" button to analyze the uploaded papers
3. **View Results**: Switch to the "View Results" tab to see the extracted dimensions
4. **Export**: Go to the "Export Data" tab to download results in your preferred format

## Extracted Dimensions

The app extracts the following dimensions from research papers:

- **DCM Capability**: Classification into one of 6 Digital Supply Chain capabilities
- **SCOR Process**: Traditional SCOR model classification (Plan, Source, Make, Deliver, Return, Enable)
- **SCRM Area**: Supply Chain Risk Management classification
- **Problem Description**: Brief description of the research problem
- **AI Technology Nature**: Type of AI technology used
- **Industry Sector**: Specific industry or sector of application

## Troubleshooting

- **Import Errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`
- **API Errors**: Verify your Anthropic API key is correctly set in the `.env` file
- **File Upload Issues**: Ensure PDFs are not password-protected or corrupted
