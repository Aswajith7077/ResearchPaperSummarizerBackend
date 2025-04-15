from fastapi import UploadFile
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import secrets
from io import BytesIO

from algorithms.reference import extract_references_from_pdf, parse_reference_as_list, optimize_urls
from algorithms.summarization import extract_text_from_pdf, clean_text, generate_summary, extract_highlights, \
    extract_keywords

schedule_queue = dict()


def find_project_root():
    """Find the project root directory by looking for specific markers"""
    current_path = Path(os.path.abspath(__file__)).parent

    # Try going up directories until you find a marker of your project root
    # This could be a specific file or directory that exists only in your project root
    # Examples: .git, pyproject.toml, setup.py, etc.
    while current_path != current_path.parent:
        if (current_path / "pyproject.toml").exists() or \
                (current_path / "setup.py").exists() or \
                (current_path / ".git").exists():
            return current_path
        current_path = current_path.parent

    # If no marker is found, return the directory containing this file

    return Path(os.path.abspath(__file__)).parent


project_root = find_project_root()
templates_dir = project_root / "templates"
templates = Jinja2Templates(directory=templates_dir)

def generateKey():
    while True:
        key = secrets.randbelow(10**12)
        if key not in schedule_queue:
            return key

async def schedule(files:list[UploadFile]):

    key = generateKey()
    schedule_queue[key] = files
    return key



async def generate_markdown(file_data):

    pdf = BytesIO(file_data)
    raw_data = extract_text_from_pdf(pdf)
    cleaned_data = clean_text(raw_data)

    if not cleaned_data:
        return """No Readable Text Found in this PDF"""

    word_count = len(cleaned_data.split())
    paragraph_count = cleaned_data.count('\n\n') + 1

    summary = generate_summary(cleaned_data)
    insights = generate_summary(cleaned_data,sentences_count = 3)



    method_section = ""
    for para in cleaned_data.split('\n\n'):
        if any(word in para.lower() for word in
               ['method', 'experiment', 'procedure', 'dataset']):
            method_section += para + "\n\n"

    if method_section:
        method_summary = generate_summary(cleaned_data,sentences_count = 4)
    else:
        method_summary = "No explicit methodology section found"



    # Key Findings

    key_findings = []
    findings = extract_highlights(cleaned_data, 5)
    for i, finding in enumerate(findings, 1):
        key_findings.append(f"Finding {i + 1}: {finding}")



    # Technical Terms

    terms = [kw for kw in extract_keywords(cleaned_data, 15)
             if kw.isupper() or len(kw.split()) > 1]


    # Extract References

    extract_references_from_pdf(pdf)
    references = parse_reference_as_list()
    urls = optimize_urls(references)

    references_urls = []
    n = len(urls)
    for i in range(n):
        references_urls.append({"text":references[i],"link":urls[i]['url']})


    print(references_urls)

    # Example data - replace with your actual data
    summary_data = {
        'MainTitle': "Structured Summary",
        'count': word_count,
        'paragraphs': paragraph_count,
        'subtitle1': "Comprehensive Summary",
        'content1': summary,
        'subtitle2': "Key Insights",
        'content2': insights,
        'subtitle3': "Methodology Highlights",
        'content3': method_summary,
        'subtitle4': "Key Findings",
        'findings': key_findings,
        'subtitle5': "Technical Terms",
        'terms': terms,
        'subtitle6': "References",
        'references': references_urls
    }

    # Read the markdown template
    with open(os.path.join(templates_dir, "summary.md"), "r") as file:
        template_content = file.read()

    # Manually replace placeholders in the template
    content = template_content
    content = content.replace("{{ MainTitle }}", summary_data['MainTitle'])
    content = content.replace("{{ count }}", str(summary_data['count']))
    content = content.replace("{{ paragraphs }}", str(summary_data['paragraphs']))

    # Replace section titles and content
    content = content.replace("{{ subtitle1 }}", summary_data['subtitle1'])
    content = content.replace("{{ content1 }}", summary_data['content1'])
    content = content.replace("{{ subtitle2 }}", summary_data['subtitle2'])
    content = content.replace("{{ content2 }}", summary_data['content2'])
    content = content.replace("{{ subtitle3 }}", summary_data['subtitle3'])
    content = content.replace("{{ content3 }}", summary_data['content3'])
    content = content.replace("{{ subtitle4 }}", summary_data['subtitle4'])
    content = content.replace("{{ subtitle5 }}", summary_data['subtitle5'])
    content = content.replace("{{ subtitle6 }}", summary_data['subtitle6'])

    # Handle lists with manual replacements
    findings_html = ""
    for finding in summary_data['findings']:
        findings_html += f"- {finding}\n"

    # Replace the Jinja for-loop with the generated HTML
    content = content.replace("{% for finding in findings %}\n- {{ finding }}\n{% endfor %}", findings_html)

    # Handle technical terms
    terms_html = ""
    for term in summary_data['terms']:
        terms_html += f'<span style="background-color: #e9f2fd; padding: 6px 12px; border-radius: 15px; font-size: 14px; color: #2980b9;">{term}</span>\n'

    content = content.replace(
        "{% for term in terms %}\n<span style=\"background-color: #e9f2fd; padding: 6px 12px; border-radius: 15px; font-size: 14px; color: #2980b9;\">{{ term }}</span>\n{% endfor %}",
        terms_html)

    # Handle references
    refs_html = ""
    for i, ref in enumerate(summary_data['references'], 1):
        refs_html += f"{i}. {ref['text']} [Link]({ref['link']})\n"

    content = content.replace(
        "{% for ref in references %}\n{{ loop.index }}. {{ ref.text }} [Link]({{ ref.link }})\n{% endfor %}",
        refs_html)

    return content



