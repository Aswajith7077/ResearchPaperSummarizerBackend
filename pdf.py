import PyPDF4
import re

path = "C:/Users/ASWAJITH/Downloads/Continuous-bag-of-words_and_Skip-gram_for_word_vec.pdf"

with open(path, 'rb') as pdfFileObj:
    pdfReader = PyPDF4.PdfFileReader(pdfFileObj)

    full_text = ""
    for i in range(pdfReader.numPages):
        page = pdfReader.getPage(i)
        full_text += page.extractText()

# Normalize text for better matching
normalized_text = full_text.lower()

# Try to find the index of "references" or "bibliography"
match = re.search(r'\b((R|r)eference(s)?|(B|b)ibliography)\b', normalized_text)

if match:
    start_idx = match.start()
    references_text = full_text[start_idx:].strip()

    print("\n[Extracted References Section]\n")
    print(references_text[:3000])  # Print first 3000 chars (adjust as needed)
else:
    print("No 'References' section found.")
