import streamlit as st
import pytesseract
from PIL import Image
import io
from fpdf import FPDF
import ollama
import time

# --- 1. UI SETUP & CONFIGURATION ---
st.set_page_config(
    page_title="NewsTrans | Editorial AI",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #FAFAFA; color: #111111; }
    h1, h2, h3, h4 { font-family: 'Georgia', serif; }
    .stButton>button { background-color: #8B0000; color: white; font-weight: bold; }
    .stButton>button:hover { background-color: #A52A2A; color: white; }
    .stTextArea textarea { font-family: 'Georgia', serif; font-size: 16px; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)


# --- 2. CORE AI & PROCESSING FUNCTIONS ---

@st.cache_data(show_spinner=False)
def extract_tamil_text(_image):
    """Extracts Tamil text using Tesseract OCR."""
    try:
        return pytesseract.image_to_string(_image, lang='tam')
    except Exception as e:
        return f"OCR Error: {e}. Please ensure Tesseract and the Tamil 'tam' language pack are installed."

def generate_headlines(raw_tamil, tone):
    """AI Headline Generator: Suggests multiple headline options."""
    prompt = f"Based on this Tamil news text, generate 3 punchy, professional English news headlines in a '{tone}' tone. Just list the 3 headlines numbered 1, 2, 3.\nText: {raw_tamil}"
    try:
        response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
    except Exception:
        return "1. [Headline generation failed]\n2. [Check AI connection]\n3. [Draft your own headline]"

def translate_article(raw_tamil, format_mode, dialect_awareness):
    """Contextual AI Translation Engine with Language Intelligence."""
    
    # Language Intelligence Layer: Adjust prompt based on dialect handling
    dialect_instruction = ""
    if dialect_awareness:
        dialect_instruction = "Pay special attention to regional Tamil dialects, local slang, and cultural references. Expand Tamil abbreviations into their proper English forms."

    # Editorial Formatting Modes
    if format_mode == "Indian Express Style":
        system_prompt = f"""You are a senior editor for The Indian Express. Translate the Tamil news text to English.
        {dialect_instruction}
        Rules:
        1. Use sharp, professional journalistic phrasing.
        2. Maintain a neutral, factual tone without sounding like a literal translation.
        3. Do NOT include a headline (that is handled separately). Just write the article body paragraphs."""
    else:
        system_prompt = f"""You are a news translator. Translate the Tamil news text into standard, clear English.
        {dialect_instruction}
        Structure it neatly into well-spaced body paragraphs."""

    try:
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"Tamil News Text:\n{raw_tamil}"}
        ])
        return response['message']['content']
    except Exception as e:
        return f"AI Translation Error: {e}"

def fact_consistency_check(original_tamil, translated_english):
    """AI Fact Checker: Ensures numbers, names, and places match."""
    prompt = f"""You are a fact-checker. Compare the original Tamil text and the English translation. 
    Verify that all names, locations, dates, and numbers match perfectly. 
    Point out any discrepancies briefly. If it looks accurate, reply '✅ Fact Check Passed: Numbers and entities appear consistent.'
    
    Tamil: {original_tamil}
    English: {translated_english}"""
    
    try:
        response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
    except Exception:
        return "Fact check unavailable."

def generate_pdf(image, headline, article_text):
    """Smart PDF Generator."""
    pdf = FPDF()
    pdf.add_page()
    
    # Image at top
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    pdf.image(img_byte_arr, x=10, y=10, w=190)
    pdf.ln(130)
    
    # Headline
    pdf.set_font("Arial", 'B', 16)
    clean_headline = headline.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_headline, align='C')
    pdf.ln(5)
    
    # Body Text
    pdf.set_font("Arial", size=11)
    clean_text = article_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    
    return pdf.output(dest='S').encode('latin-1')


# --- 3. FRONTEND UI & WORKFLOW ---

st.title("📰 NewsTrans")
st.markdown("### Intelligent Tamil-to-English Editorial Translation")

with st.sidebar:
    st.header("⚙️ Translation Settings")
    format_mode = st.radio("Editorial Mode:", ("Standard News Format", "Indian Express Style"), index=1)
    
    st.markdown("---")
    st.header("🧠 Advanced Features")
    dialect_awareness = st.checkbox("🌐 Language Intelligence (Dialect Handling)", value=True)
    enable_fact_check = st.checkbox("🔍 Fact Consistency Checker", value=True)

uploaded_files = st.file_uploader(
    "📤 Upload Tamil Newspaper Clippings (Batch Supported)", 
    type=['png', 'jpg', 'jpeg'], 
    accept_multiple_files=True
)

if uploaded_files:
    st.markdown("---")
    
    for idx, uploaded_file in enumerate(uploaded_files):
        st.subheader(f"📄 Document {idx + 1}: {uploaded_file.name}")
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns([1, 1.2])
        
        # Unique session state keys for batch processing
        raw_key = f"raw_{uploaded_file.name}"
        hl_key = f"hl_{uploaded_file.name}"
        body_key = f"body_{uploaded_file.name}"
        fact_key = f"fact_{uploaded_file.name}"
        
        with col1:
            st.image(image, use_container_width=True)
            
            if st.button("🚀 Process & Translate", key=f"btn_{uploaded_file.name}"):
                
                # 1. Extract Text
                with st.spinner("Extracting Tamil Text via OCR..."):
                    raw_tamil = extract_tamil_text(image)
                    st.session_state[raw_key] = raw_tamil
                
                if raw_tamil.strip() and not raw_tamil.startswith("OCR Error"):
                    # 2. Generate Headlines
                    with st.spinner("Generating Headline Options..."):
                        st.session_state[hl_key] = generate_headlines(raw_tamil, format_mode)
                    
                    # 3. Translate Article Body
                    with st.spinner(f"Rewriting Body in {format_mode}..."):
                        st.session_state[body_key] = translate_article(raw_tamil, format_mode, dialect_awareness)
                    
                    # 4. Fact Check (If enabled)
                    if enable_fact_check:
                        with st.spinner("Running Fact Consistency Checker..."):
                            st.session_state[fact_key] = fact_consistency_check(raw_tamil, st.session_state[body_key])
                
                elif raw_tamil.startswith("OCR Error"):
                    st.error(raw_tamil)
                else:
                    st.warning("No text detected. Please upload a clearer clipping.")

        with col2:
            if body_key in st.session_state:
                st.markdown("### 📝 Editing & Review Interface")
                
                # Headline Selection/Editing
                st.info("**AI Headline Suggestions:**\n\n" + st.session_state[hl_key])
                final_headline = st.text_input("Enter Final Headline:", placeholder="Type or paste your chosen headline here...", key=f"edit_hl_{uploaded_file.name}")
                
                # Article Body Editing
                final_body = st.text_area("Refined Article Body:", value=st.session_state[body_key], height=300, key=f"edit_body_{uploaded_file.name}")
                
                # Fact Check Results
                if enable_fact_check and fact_key in st.session_state:
                    with st.expander("🛡️ View Fact Consistency Report", expanded=True):
                        st.write(st.session_state[fact_key])
                
                # Original Text Toggle
                with st.expander("🔍 View Raw Tamil OCR"):
                    st.write(st.session_state[raw_key])
                
                # Smart PDF Export
                if final_headline and final_body:
                    pdf_bytes = generate_pdf(image, final_headline, final_body)
                    st.download_button(
                        label="📥 Download Publication-Ready PDF",
                        data=pdf_bytes,
                        file_name=f"Translated_{uploaded_file.name.split('.')[0]}.pdf",
                        mime="application/pdf",
                        key=f"dl_{uploaded_file.name}"
                    )
                else:
                    st.caption("Please enter a headline to enable PDF download.")
        
        st.markdown("---")
else:
    st.info("Upload one or more Tamil newspaper images to start the translation engine.")

