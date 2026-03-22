import streamlit as st
import pytesseract
from PIL import Image
import io
from fpdf import FPDF
import ollama
import time

# --- 1. UI CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="NewsTrans | Editorial AI",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, newsroom-style CSS
st.markdown("""
    <style>
    .stApp { background-color: #FAFAFA; color: #333333; }
    h1, h2, h3, h4 { font-family: 'Georgia', serif; }
    .stButton>button { background-color: #8B0000; color: white; border-radius: 5px; font-weight: bold; }
    .stButton>button:hover { background-color: #A52A2A; color: white; }
    .stTextArea textarea { font-family: 'Georgia', serif; font-size: 16px; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)


# --- 2. CORE PROCESSING FUNCTIONS ---

@st.cache_data(show_spinner=False)
def extract_tamil_text(_image):
    """Extracts Tamil text using Tesseract OCR. Cached to prevent re-running on UI updates."""
    try:
        # Note: 'tam' language pack must be installed on your OS
        text = pytesseract.image_to_string(_image, lang='tam')
        return text
    except Exception as e:
        return f"OCR Error: {e}. Please ensure Tesseract and the Tamil language pack are installed."

def rewrite_article(raw_tamil, format_mode):
    """Uses Ollama (Local AI) to translate and format the text."""
    
    if format_mode == "Indian Express Style":
        system_prompt = """You are a senior editor for an elite Indian English newspaper (like The Indian Express). 
        Translate the provided Tamil news text to English. 
        Rules:
        1. Create a sharp, concise, and punchy headline.
        2. Use professional, objective journalistic phrasing.
        3. Maintain a neutral, factual tone. 
        4. Do not make it sound like a literal translation; it must flow naturally for native English readers.
        5. Format clearly with 'HEADLINE:' followed by the body paragraphs."""
    else:
        system_prompt = """You are a professional news translator. 
        Translate the provided Tamil news text into clear, standard English. 
        Structure it neatly with a main Headline and well-spaced body paragraphs. Ensure grammar and context are correct."""

    try:
        # Calls the local Ollama instance. Assuming 'llama3' is pulled.
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"Tamil News Text:\n{raw_tamil}"}
        ])
        return response['message']['content']
    except Exception as e:
        return f"AI Translation Error. Ensure the Ollama app is running locally. Details: {e}"

def generate_pdf(image, english_text, filename="Translated_News.pdf"):
    """Generates a downloadable PDF containing the source image and translated text."""
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Add Image at the top
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    pdf.image(img_byte_arr, x=10, y=10, w=190)
    
    # Move cursor below image 
    pdf.ln(130)
    
    # 2. Add English Text
    pdf.set_font("Arial", size=11)
    # Clean text to prevent PDF encoding errors
    cleaned_text = english_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=cleaned_text)
    
    return pdf.output(dest='S').encode('latin-1')


# --- 3. APP LAYOUT & LOGIC ---

st.title("📰 NewsTrans")
st.markdown("### Journalist-Grade Tamil to English Translation")
st.write("Upload Tamil newspaper clippings and transform them into publication-ready English articles.")

# Sidebar Settings
with st.sidebar:
    st.header("🎛️ Editorial Settings")
    format_mode = st.radio(
        "Select Formatting Mode:",
        ("Standard News Format", "Indian Express Style"),
        index=1
    )
    st.markdown("---")
    st.info("**System Check:**\n1. Ensure Tesseract OCR is installed.\n2. Ensure Ollama is running in the background with the `llama3` model.")

# Main Upload Section
uploaded_files = st.file_uploader(
    "📤 Upload Tamil Newspaper Images (Batch Upload Supported)", 
    type=['png', 'jpg', 'jpeg'], 
    accept_multiple_files=True
)

if uploaded_files:
    st.markdown("---")
    
    # Loop through all uploaded files (Batch Processing capability)
    for idx, uploaded_file in enumerate(uploaded_files):
        st.subheader(f"📄 Document {idx + 1}: {uploaded_file.name}")
        image = Image.open(uploaded_file)
        
        # Split layout into two columns: Original vs Translated
        col1, col2 = st.columns(2)
        
        # State management keys for this specific file
        raw_key = f"raw_{uploaded_file.name}"
        trans_key = f"trans_{uploaded_file.name}"
        
        with col1:
            st.markdown("**Original Tamil Image**")
            st.image(image, use_container_width=True)
            
            if st.button(f"Extract & Translate Document {idx + 1}", key=f"btn_{uploaded_file.name}"):
                
                # Step 1: OCR Extraction
                with st.spinner("🔍 Running advanced OCR..."):
                    raw_tamil = extract_tamil_text(image)
                    st.session_state[raw_key] = raw_tamil
                
                # Step 2: AI Translation
                if raw_tamil.strip() and not raw_tamil.startswith("OCR Error"):
                    with st.spinner(f"✍️ Rewriting in {format_mode}..."):
                        english_translation = rewrite_article(raw_tamil, format_mode)
                        st.session_state[trans_key] = english_translation
                elif raw_tamil.startswith("OCR Error"):
                    st.error(raw_tamil)
                else:
                    st.warning("No text detected in the image. Please upload a clearer clipping.")

        with col2:
            st.markdown("**Live Translated Article**")
            
            # If translation exists in session state, show the editor and PDF downloader
            if trans_key in st.session_state:
                # Interactive Editor
                edited_text = st.text_area(
                    "Review and Edit (Publication Ready):", 
                    value=st.session_state[trans_key], 
                    height=350,
                    key=f"edit_{uploaded_file.name}"
                )
                
                # PDF Generation on the fly based on edited text
                pdf_bytes = generate_pdf(image, edited_text)
                
                st.download_button(
                    label="📄 Download as PDF",
                    data=pdf_bytes,
                    file_name=f"Translated_{uploaded_file.name.split('.')[0]}.pdf",
                    mime="application/pdf",
                    key=f"dl_{uploaded_file.name}"
                )
                
                # Collapsible raw text view for fact-checking
                with st.expander("🔍 View Raw OCR Output (Tamil)"):
                    st.write(st.session_state.get(raw_key, "No raw text available."))
        
        st.markdown("---") # Divider between batch documents

else:
    # Empty state placeholder
    st.info("👆 Upload one or more Tamil newspaper images to begin.")
