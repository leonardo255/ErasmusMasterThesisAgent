import streamlit as st
import os
import json
import tempfile
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import sys

# Add app directory to path to import src modules
sys.path.append(str(Path(__file__).parent))

from src.agents.prompt import SYS_PROMPT
from src.agents.dimension_extractor import DimensionExtractor
from src.parse_papers import chunk_pdf

# Load environment variables
load_dotenv()

# Assets path
assets_dir = Path(__file__).parent / "assets" / "images"

# Page configuration
st.set_page_config(
    page_title="Research Paper Analyzer",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'processed_papers' not in st.session_state:
    st.session_state.processed_papers = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []
if 'custom_prompt' not in st.session_state:
    st.session_state.custom_prompt = SYS_PROMPT

# Initialize LLM model
def initialize_model():
    """Initialize the Anthropic chat model."""
    return init_chat_model(
        "anthropic:claude-haiku-4-5",
        temperature=0.5,
        timeout=30,
        max_tokens=5000,
    )

# Initialize extractor agent
def initialize_agent(sys_prompt):
    """Initialize the dimension extractor agent with optional custom prompt."""
    model = initialize_model()
    return DimensionExtractor(model=model, sys_prompt=sys_prompt)

# Main app
def main():
    st.title("Research Paper Analyzer")
    st.markdown("Upload PDF research papers to extract structured dimensions using AI.")
    
    # Sidebar
    with st.sidebar:
        # Display SDU logo at the top
        sdu_logo_path = assets_dir / "sdu_logo.png"
        if sdu_logo_path.exists():
            st.image(str(sdu_logo_path), use_container_width=True)
        
        st.header("⚙️ Settings")
        
        # System Prompt Editor
        with st.expander("Edit System Prompt", expanded=False):
            st.markdown("Customize the instructions given to the AI agent:")
            
            custom_prompt = st.text_area(
                "System Prompt",
                value=st.session_state.custom_prompt,
                height=400,
                help="Edit the system prompt to customize how the AI analyzes papers",
                key="prompt_editor"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Prompt", use_container_width=True):
                    st.session_state.custom_prompt = custom_prompt
                    st.success("Prompt saved!")
            with col2:
                if st.button("Reset to Default", use_container_width=True):
                    st.session_state.custom_prompt = SYS_PROMPT
                    st.success("Prompt reset to default!")
                    st.rerun()

        
        st.markdown("### About")
        st.info(
            "This tool analyzes research papers on supply chain management "
            "and AI, extracting key dimensions such as DCM capabilities, "
            "SCOR processes, and AI technologies used."
        )
        
        if st.button("Clear All Data"):
            st.session_state.processed_papers = []
            st.session_state.analysis_results = []
            st.success("Data cleared!")
            st.rerun()
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "📊 View Results", "💾 Export Data"])
    
    # Tab 1: Upload and Process
    with tab1:
        st.header("Upload PDF Files")
        
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload one or more PDF research papers"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
            
            # Display uploaded files
            with st.expander("View uploaded files"):
                for file in uploaded_files:
                    st.write(f"- {file.name} ({file.size / 1024:.1f} KB)")
            
            # Show if using custom prompt
            if st.session_state.custom_prompt != SYS_PROMPT:
                st.info("ℹ️ Using custom system prompt. Edit in Settings sidebar.")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                process_button = st.button("Process Papers", type="primary", use_container_width=True)
            
            if process_button:
                process_papers(uploaded_files)
    
    # Tab 2: View Results
    with tab2:
        st.header("Analysis Results")
        
        if st.session_state.analysis_results:
            st.success(f"📊 {len(st.session_state.analysis_results)} paper(s) analyzed")
            
            for idx, result in enumerate(st.session_state.analysis_results):
                with st.expander(f"📄 {result.get('filename', f'Paper {idx+1}')}"):
                    display_result(result)
        else:
            st.info("No results yet. Upload and process papers in the 'Upload & Process' tab.")
    
    # Tab 3: Export Data
    with tab3:
        st.header("Export Results")
        
        if st.session_state.analysis_results:
            export_format = st.radio(
                "Select export format:",
                ["JSON", "CSV", "Excel"],
                horizontal=True
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if export_format == "JSON":
                    json_data = json.dumps(st.session_state.analysis_results, indent=2)
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_data,
                        file_name="analysis_results.json",
                        mime="application/json",
                        use_container_width=True
                    )
                    
            with col2:
                if export_format == "CSV":
                    df = results_to_dataframe(st.session_state.analysis_results)
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name="analysis_results.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                elif export_format == "Excel":
                    df = results_to_dataframe(st.session_state.analysis_results)
                    # Create Excel file in memory
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Analysis Results')
                    excel_data = output.getvalue()
                    st.download_button(
                        label="⬇️ Download Excel",
                        data=excel_data,
                        file_name="analysis_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            # Display preview
            st.subheader("Preview")
            if export_format in ["CSV", "Excel"]:
                df = results_to_dataframe(st.session_state.analysis_results)
                st.dataframe(df, use_container_width=True)
            else:
                st.json(st.session_state.analysis_results)
                
            # Copy to clipboard option
            st.subheader("Copy Data")
            if export_format == "JSON":
                json_text = json.dumps(st.session_state.analysis_results, indent=2)
                st.text_area("JSON Output (copy this)", json_text, height=300)
        else:
            st.info("No results to export. Process some papers first.")


def process_papers(uploaded_files):
    """Process uploaded PDF files."""
    try:
        # Initialize agent with custom prompt from session state
        agent = initialize_agent(sys_prompt=st.session_state.custom_prompt)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_files = len(uploaded_files)
        
        for idx, uploaded_file in enumerate(uploaded_files):
            filename = uploaded_file.name
            status_text.text(f"Processing {filename}... ({idx+1}/{total_files})")
            
            # Create temporary file to save uploaded PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            
            try:
                # Step 1: Parse PDF to chunks
                with st.spinner(f"📖 Parsing {filename}..."):
                    parsed_data = chunk_pdf(tmp_path)
                
                # Add filename to metadata
                parsed_data['metadata']['source']['filename'] = filename
                
                # Step 2: Analyze with extractor agent
                with st.spinner(f"🤖 Analyzing {filename}..."):
                    analysis_result = agent.go_to_work(
                        user_instructions="Please analyze and extract the following dimensions from this research paper:",
                        input_data=parsed_data
                    )
                
                # Combine results
                result_data = {
                    'filename': filename,
                    'metadata': parsed_data.get('metadata', {}),
                    'analysis': analysis_result
                }
                
                st.session_state.analysis_results.append(result_data)
                st.session_state.processed_papers.append(filename)
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
            
            # Update progress
            progress_bar.progress((idx + 1) / total_files)
        
        status_text.text("✅ Processing complete!")
        st.success(f"Successfully processed {total_files} paper(s)!")
        
        # Auto-switch to results tab would require additional logic
        st.balloons()
        
    except Exception as e:
        st.error(f"Error processing papers: {str(e)}")
        st.exception(e)


def display_result(result):
    """Display analysis result for a single paper."""
    st.subheader("📋 Metadata")
    metadata = result.get('metadata', {}).get('source', {})
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Chunks", metadata.get('n_chunks', 'N/A'))
    with col2:
        timestamp = metadata.get('timestamp', 'N/A')
        if timestamp != 'N/A':
            timestamp = timestamp.split('T')[0]  # Show only date
        st.metric("Processed", timestamp)
    
    st.subheader("🔍 Analysis Results")
    analysis = result.get('analysis', {})
    
    if 'error' in analysis:
        st.error(f"Analysis error: {analysis['error']}")
        if 'raw_output' in analysis:
            with st.expander("Raw output"):
                st.text(analysis['raw_output'])
    else:
        # Display all extracted dimensions
        display_dict = {}
        for key, value in analysis.items():
            if value is not None:
                display_dict[key.replace('_', ' ').title()] = value
        
        if display_dict:
            st.json(display_dict)
        else:
            st.warning("No dimensions extracted from this paper.")


def results_to_dataframe(results):
    """Convert analysis results to a pandas DataFrame."""
    rows = []
    
    for result in results:
        analysis = result.get('analysis', {})
        metadata = result.get('metadata', {}).get('source', {})
        
        row = {
            'Filename': result.get('filename', 'N/A'),
            'Timestamp': metadata.get('timestamp', 'N/A'),
            'N_Chunks': metadata.get('n_chunks', 'N/A'),
            'DCM Capability': analysis.get('dcm_capability', ''),
            'SCOR Process': analysis.get('scor_process', ''),
            'SCRM Area': analysis.get('scrm_area', ''),
            'Problem Description': analysis.get('problem_description', ''),
            'AI Technology Nature': analysis.get('ai_technology_nature', ''),
            'Industry Sector': analysis.get('industry_sector', ''),
        }
        
        rows.append(row)
    
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
