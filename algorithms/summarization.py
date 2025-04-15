import streamlit as st
import pdfplumber
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from rake_nltk import Rake
import nltk
import re
import logging

# Suppress pdfplumber CropBox warnings
logging.getLogger("pdfplumber").setLevel(logging.ERROR)

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)





# # Download required NLTK data

def extract_text_from_pdf(pdf_file):
    """Improved text extraction with paragraph handling"""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True)  # Preserve layout
            if page_text:
                text += page_text + "\n\n"
    return text.strip()


def clean_text(text):
    """Enhanced cleaning for academic papers"""
    # Remove citations and references
    text = re.sub(r'\([^)]*\)', '', text)  # Remove parenthetical citations
    text = re.sub(r'\[[^\]]*\]', '', text)  # Remove bracket citations
    # Remove email patterns and URLs
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'http\S+|www\S+', '', text)
    # Normalize whitespace but preserve paragraph breaks
    text = re.sub(r'[^\S\n]+', ' ', text)  # Single space except newlines
    text = re.sub(r'\n\s+\n', '\n\n', text)  # Clean paragraph breaks
    # Remove special characters except basic punctuation
    text = re.sub(r'[^\w\s.,;:!?\'"-]', '', text)
    return text.strip()


def extract_keywords(text, n=10):
    """Improved keyword extraction for academic content"""
    r = Rake(
        min_length=1,
        max_length=3,  # Allow multi-word phrases
        include_repeated_phrases=False
    )
    r.extract_keywords_from_text(text)
    return [kw for kw in r.get_ranked_phrases()
            if len(kw.split()) <= 3][:n]  # Only phrases up to 3 words


def generate_summary(text, sentences_count=7):
    """Improved academic paper summarization"""
    # Pre-process to remove noisy elements
    clean_content = re.sub(r'\b(Figure|Table)\s+\d+[.:].*', '', text)
    clean_content = re.sub(r'\bDOI:.+', '', clean_content)

    parser = PlaintextParser.from_string(clean_content, Tokenizer("english"))
    summarizer = LexRankSummarizer()

    # Get summary and post-process
    summary = summarizer(parser.document, sentences_count)
    summary_sentences = [str(s) for s in summary]

    # Remove short or incomplete sentences
    return " ".join([s for s in summary_sentences
                     if len(s.split()) > 5 and s.endswith(('.', '!', '?'))])


def extract_highlights(text, n=5):
    """Academic paper highlights with context awareness"""
    # Split into sections
    sections = re.split(r'\n\n+', text)
    important_sentences = []

    for section in sections:
        sentences = nltk.sent_tokenize(section)
        if len(sentences) < 3:
            continue

        # Score sentences by position and length
        for i, sent in enumerate(sentences):
            score = 0
            # Higher score for opening/closing sentences
            if i == 0 or i == len(sentences) - 1:
                score += 1
            # Higher score for longer sentences
            score += min(len(sent.split()) / 20, 1)  # Normalize by 20 words
            important_sentences.append((sent, score))

    # Sort and select top sentences
    important_sentences.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in important_sentences[:n]]


def main():
    st.set_page_config(
        page_title="Academic PDF Summarizer",
        page_icon="📚",
        layout="wide"
    )

    st.title("Academic Paper Summarizer")
    st.markdown("""
        <style>
            .reportview-container .main footer {visibility: hidden;}
            .block-container {padding-top: 1rem; padding-bottom: 1rem;}
            .highlight {
                background-color: #f5f5f5;
                border-left: 4px solid #ff4b4b;
                padding: 0.5rem 1rem;
                margin: 1rem 0;
            }
        </style>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload academic PDF", type="pdf")

    if uploaded_file:
        with st.spinner("Processing academic paper..."):
            try:
                raw_text = extract_text_from_pdf(uploaded_file)
                cleaned_text = clean_text(raw_text)

                if not cleaned_text:
                    st.warning("No readable text found in this PDF")
                    return

                # Document metadata
                st.subheader("Paper Overview")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Word Count", f"{len(cleaned_text.split()):,}")
                    st.metric("Paragraphs", cleaned_text.count('\n\n') + 1)
                with col2:
                    keywords = extract_keywords(cleaned_text)
                    st.metric("Key Terms", ", ".join(keywords[:3]))

                # Main summary
                st.subheader("Structured Summary")

                with st.expander("📖 Comprehensive Summary", expanded=True):
                    summary = generate_summary(cleaned_text)
                    st.write(summary)

                with st.expander("💡 Key Insights"):
                    insights = generate_summary(cleaned_text, sentences_count=3)
                    st.markdown(f"<div class='highlight'>{insights}</div>",
                                unsafe_allow_html=True)

                with st.expander("🔬 Methodology Highlights"):
                    method_section = ""
                    for para in cleaned_text.split('\n\n'):
                        if any(word in para.lower() for word in
                               ['method', 'experiment', 'procedure', 'dataset']):
                            method_section += para + "\n\n"
                    if method_section:
                        method_summary = generate_summary(method_section, 4)
                        st.write(method_summary)
                    else:
                        st.info("No explicit methodology section found")

                with st.expander("📊 Key Findings"):
                    findings = extract_highlights(cleaned_text, 5)
                    for i, finding in enumerate(findings, 1):
                        st.markdown(f"{i}. {finding}")

                with st.expander("📝 Technical Terms"):
                    terms = [kw for kw in extract_keywords(cleaned_text, 15)
                             if kw.isupper() or len(kw.split()) > 1]
                    st.write(", ".join(terms))

            except Exception as e:
                st.error(f"Processing error: {str(e)}")
                st.info("Try a different PDF or check console for details")


if __name__ == "__main__":
    main()