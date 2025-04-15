import re
import requests
import os
import pdfplumber
import numpy as np
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup


# Initialize SentenceTransformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

def parse_reference_as_list():
    with open("extracted_references.txt", "r", encoding='utf-8') as file:
        data = file.read()
        print("Raw data:")
        print(data)
        references = []
        current_ref = ""
        for line in data.split("\n")[1:]:
            line = line.strip()
            if line.startswith("[") and re.match(r'\[\d+\]', line):
                if current_ref:
                    references.append(current_ref.strip())
                current_ref = line
            else:
                current_ref += " " + line
        if current_ref:
            references.append(current_ref.strip())
        final = [ref for ref in references if ref]

    return final

def optimize_urls(final):
    all_scores = []
    for ref in final:
        try:
            parsed = parse_reference(ref)
            print(f"\nReference: {ref}")
            print(f"Parsed: {parsed}")
            urls = search_resource(parsed)
            print(f"URLs: {urls}")
            scores = score_links(ref, urls)
            all_scores.extend(scores)
            print("Scores:")
            for s in scores:
                print(f"  URL: {s['url']}")
                print(f"    Authority: {s['authority_score']:.2f}")
                print(f"    Relevance: {s['relevance_score']:.2f}")
                print(f"    Total: {s['total_score']:.2f}")
        except Exception as e:
            print(f"Error processing '{ref}': {e}")

    # Maximize scores (e.g., select top-scoring links)
    # print("\nTop links (sorted by total score):")
    sorted_scores = sorted(all_scores, key=lambda x: x["total_score"], reverse=True)
    # for s in sorted_scores[:5]:  # Top 5 for brevity
    #     print(f"URL: {s['url']}, Total Score: {s['total_score']:.2f}")
    return sorted_scores[:5]


def extract_references_from_pdf(pdf_path, output_file="extracted_references.txt"):
    """
    Extract the references/bibliography section from a PDF and save it to a file.

    Args:
        pdf_path (str): Path to the input PDF file.
        output_file (str): Path to save the extracted references.
    """
    # Reference section heading patterns (case-insensitive)
    reference_patterns = [
        r'^\s*(r|R)eference(s)?\s*$',
        r'^\s*(b|B)ibliography\s*$',
        r'^\s*(w|W)orks\s+(c|C)ited\s*$',
        r'^\s*(l|L)iterature\s+(c|C)ited\s*$',
        r'^\s*(r|R)eferences\s+(c|C)ited\s*$'
    ]

    # Patterns for detecting sections that might follow references
    next_section_patterns = [
        r'^\s*(a|A)ppendix\s*',
        r'^\s*(a|A)cknowledgements?\s*',
        r'^\s*(n|N)otes\s*',
        r'^\s*(a|A)bout\s+the\s+(a|A)uthor\s*',
        r'^\s*(c|C)onclusion\s*'
    ]

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = []
            references_start_page = None
            references_end_page = None
            references_start_idx = None
            references_end_idx = None

            # Extract text page by page
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                full_text.append((page_num, text))

                # Normalize text for matching
                normalized_text = text.lower().strip()

                # Check for reference section start
                if references_start_page is None:
                    for pattern in reference_patterns:
                        if re.search(pattern, normalized_text, re.MULTILINE):
                            references_start_page = page_num
                            # Find exact start index within page text
                            for line in text.split('\n'):
                                if re.search(pattern, line.lower().strip()):
                                    references_start_idx = text.index(line)
                                    break
                            break

                # Check for next section (to end references)
                if references_start_page is not None and page_num >= references_start_page:
                    for pattern in next_section_patterns:
                        if re.search(pattern, normalized_text, re.MULTILINE):
                            references_end_page = page_num
                            # Find exact end index within page text
                            for line in text.split('\n'):
                                if re.search(pattern, line.lower().strip()):
                                    references_end_idx = text.index(line)
                                    break
                            break

            if references_start_page is None:
                print("No 'References' section found.")
                # Debugging: Look for related terms
                all_text = ' '.join([t[1].lower() for t in full_text])
                potential_refs = re.findall(r'\b\w*refer\w*\b|\b\w*cite\w*\b|\b\w*bibl\w*\b', all_text)
                if potential_refs:
                    print("Potential reference-related terms:", list(set(potential_refs))[:10])
                return

            # Extract references text
            references_text = ""
            for page_num, text in full_text:
                if references_start_page is not None and references_end_page is None:
                    # References continue to the end
                    if page_num >= references_start_page:
                        if page_num == references_start_page:
                            references_text += text[references_start_idx:]
                        else:
                            references_text += text
                elif references_start_page is not None and references_end_page is not None:
                    # References are contained within pages
                    if page_num == references_start_page == references_end_page:
                        references_text += text[references_start_idx:references_end_idx]
                    elif page_num == references_start_page:
                        references_text += text[references_start_idx:]
                    elif page_num < references_end_page:
                        references_text += text
                    elif page_num == references_end_page:
                        references_text += text[:references_end_idx]

            references_text = references_text.strip()

            if not references_text:
                print("References section is empty or could not be extracted.")
                return

            # Save to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(references_text)

            print(f"References section extracted successfully.")
            print(f"Total characters in references section: {len(references_text)}")
            print(f"Saved to '{output_file}'")

            # Preview first 200 characters
            preview_length = min(200, len(references_text))
            print(f"\nPreview (first {preview_length} characters):")
            print(references_text[:preview_length] + "...")

    except FileNotFoundError:
        print(f"Error: PDF file '{pdf_path}' not found.")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

def parse_reference(ref_text):
    """Parse a reference string into title, authors, year, and venue."""
    ref_text = re.sub(r'^\[\d+\]\s*', '', ref_text)
    authors_match = re.search(r'^(.*?)\s*\(\d{4}\)', ref_text)
    authors = authors_match.group(1).strip() if authors_match else ""
    year_match = re.search(r'\((\d{4})\)', ref_text)
    year = year_match.group(1) if year_match else ""
    title_match = re.search(r'\.\s*(.*?)\.\s*(?:In\s|Advances|Proceedings|[A-Z])', ref_text, re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""
    venue_start = ref_text.find(f"({year})") + len(f"({year})") if year else len(ref_text)
    venue = ref_text[venue_start:].strip("., ").split(". ", 1)[-1].strip() if year else ""
    return {"title": title, "authors": authors, "year": year, "venue": venue}


def search_google_scholar(query):
    """
    Search Google Scholar for a query and return top 3 URLs.

    Args:
        query (str): Search query (e.g., title + authors + venue).

    Returns:
        list: List of up to 3 URLs from Google Scholar, or empty list if none found.
    """
    # Placeholder for SerpAPI key (replace with your key)
    api_key = os.getenv("SERPAPI")  # Set this in your environment

    if not api_key:
        print("Warning: SerpAPI key not found. Simulating Scholar search.")
        # Simulate results for demo (replace with real search in production)
        return [
            "https://scholar.google.com/scholar?hl=en&q=" + query.replace(" ", "+")
        ]  # Mock URL

    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": api_key,
            "num": 3
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract URLs from organic results
        urls = []
        for result in data.get("organic_results", [])[:3]:
            if "link" in result:
                urls.append(result["link"])
        return urls

    except Exception as e:
        print(f"Error searching Google Scholar: {e}")
        return []


def search_google(query):
    """
    Perform a general Google search and return the top result URL.

    Args:
        query (str): Search query.

    Returns:
        str: Top URL from Google search, or a fallback search URL.
    """
    # Placeholder for SerpAPI key
    api_key = os.getenv("SERPAPI")

    if not api_key:
        print("Warning: SerpAPI key not found. Simulating Google search.")
        # Simulate result for demo
        return "https://www.google.com/search?q=" + query.replace(" ", "+")

    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Get the top result URL
        for result in data.get("organic_results", [])[:1]:
            return result.get("link", "")

        return "https://www.google.com/search?q=" + query.replace(" ", "+")

    except Exception as e:
        print(f"Error searching Google: {e}")
        return "https://www.google.com/search?q=" + query.replace(" ", "+")

def search_resource(parsed_ref):
    """Search for resource URLs based on a parsed reference."""
    if not parsed_ref or not any(parsed_ref.get(key) for key in ['title', 'authors', 'venue']):
        print("Error: Invalid parsed reference")
        return []
    query_parts = [parsed_ref.get(field, "") for field in ['title', 'authors', 'venue'] if parsed_ref.get(field)]
    query = " ".join(query_parts).strip()
    if not query:
        print("Error: Could not construct query")
        return []
    scholar_urls = search_google_scholar(query)
    if scholar_urls:
        return scholar_urls
    if "arxiv" in parsed_ref.get('venue', '').lower():
        arxiv_match = re.search(r'arXiv:(\d+\.\d+)', parsed_ref['venue'], re.IGNORECASE)
        if arxiv_match:
            return [f"https://arxiv.org/abs/{arxiv_match.group(1)}"]
    return [search_google(query)]


def fetch_webpage_text(url, max_chars=1000):
    """Fetch and extract text from a webpage."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:max_chars]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""


def authority_score(url):
    """Assign an authority score based on URL domain."""
    trusted_domains = ["arxiv.org", "springer.com", "ieee.org", ".edu", ".gov"]
    return 1.0 if any(domain in url for domain in trusted_domains) else 0.5


def relevance_score(reference_text, webpage_text):
    """Compute relevance score between reference and webpage text."""
    if not webpage_text or not reference_text:
        return 0.0
    try:
        ref_embedding = model.encode(reference_text)
        page_embedding = model.encode(webpage_text[:500])
        similarity = np.dot(ref_embedding, page_embedding) / (
                np.linalg.norm(ref_embedding) * np.linalg.norm(page_embedding)
        )
        return max(0.0, similarity)  # Ensure non-negative
    except Exception as e:
        print(f"Error computing relevance: {e}")
        return 0.0


def score_links(reference, urls):
    """Score a list of URLs for a reference."""
    scores = []
    ref_text = reference  # Use raw reference or parsed fields
    for url in urls:
        webpage_text = fetch_webpage_text(url)
        auth_score = authority_score(url)
        rel_score = relevance_score(ref_text, webpage_text)
        total_score = auth_score * rel_score  # Combine scores
        scores.append({
            "url": url,
            "authority_score": auth_score,
            "relevance_score": rel_score,
            "total_score": total_score
        })
    return scores


def main():
    # Read references
    final = []
    with open("extracted_references.txt", "r", encoding='utf-8') as file:
        data = file.read()
        print("Raw data:")
        print(data)
        references = []
        current_ref = ""
        for line in data.split("\n"):
            line = line.strip()
            if line.startswith("[") and re.match(r'\[\d+\]', line):
                if current_ref:
                    references.append(current_ref.strip())
                current_ref = line
            else:
                current_ref += " " + line
        if current_ref:
            references.append(current_ref.strip())
        final = [ref for ref in references if ref]

    print("\nParsed references:")
    print(final)

    # Process references and score links
    all_scores = []
    for ref in final:
        try:
            parsed = parse_reference(ref)
            print(f"\nReference: {ref}")
            print(f"Parsed: {parsed}")
            urls = search_resource(parsed)
            print(f"URLs: {urls}")
            scores = score_links(ref, urls)
            all_scores.extend(scores)
            print("Scores:")
            for s in scores:
                print(f"  URL: {s['url']}")
                print(f"    Authority: {s['authority_score']:.2f}")
                print(f"    Relevance: {s['relevance_score']:.2f}")
                print(f"    Total: {s['total_score']:.2f}")
        except Exception as e:
            print(f"Error processing '{ref}': {e}")

    # Maximize scores (e.g., select top-scoring links)
    print("\nTop links (sorted by total score):")
    sorted_scores = sorted(all_scores, key=lambda x: x["total_score"], reverse=True)
    for s in sorted_scores[:5]:  # Top 5 for brevity
        print(f"URL: {s['url']}, Total Score: {s['total_score']:.2f}")


if __name__ == "__main__":
    main()