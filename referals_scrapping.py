import os

import requests
import fitz  # PyMuPDF for PDF handling
import random
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Define constants
ALPHA = 0.5  # Relevance weight
BETA = 0.5  # Authority weight
DISCOUNT_FACTOR = 0.9  # For Q-learning
EPSILON = 0.1  # Exploration rate (for Q-learning)

# Seed research papers (URLs or metadata)
seed_papers = [
    # "https://www.researchgate.net/publication/329390711_Dynamic_programming",
    "https://arxiv.org/pdf/2205.10490.pdf",  # Example PDF links
    # "https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9185221",  # Another PDF link
    # Add more URLs of research papers (PDFs)
]

# Initialize the Q-table for Q-learning (state-action value function)
q_table = {}  # Dictionary of Q-values for each (state, action)


# A function to extract content from a PDF file URL
def extract_pdf_content(url):
    response = requests.get(url)

    # Save the PDF to a local file temporarily
    pdf_path = "temp_paper.pdf"
    print(os.listdir('.'))
    with open(pdf_path, 'wb') as f:
        f.write(response.content)

    # Use PyMuPDF (fitz) to extract text from the PDF
    doc = fitz.open(pdf_path)
    content = ""
    for page in doc:
        content += page.get_text()  # Extract text from each page of the PDF

    return content


# Relevance scoring using TF-IDF
def calculate_relevance(query, content):
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform([query, content])

    # Cosine similarity between query and content
    similarity = (tfidf_matrix[0] * tfidf_matrix[1].T).toarray()[0][0]
    return similarity


# Authority scoring (simplified, just based on citations for example)
def calculate_authority(url):
    # Mocking authority scoring (can be based on citation count or journal impact factor)
    citation_count = random.randint(10, 500)  # Mock citation count for simplicity
    return citation_count


# Q-learning: Update Q-value
def update_q_value(state, action, reward, next_state):
    # Initialize Q-table entry if not already present
    if state not in q_table:
        q_table[state] = {}
    if action not in q_table[state]:
        q_table[state][action] = 0

    # Q-learning formula: Q(s, a) = Q(s, a) + α * (reward + γ * max_a' Q(s', a') - Q(s, a))
    max_future_q = max(q_table.get(next_state, {}).values(), default=0)
    q_table[state][action] = q_table[state][action] + ALPHA * (
                reward + DISCOUNT_FACTOR * max_future_q - q_table[state][action])


# Choose action based on epsilon-greedy policy
def choose_action(state, actions):
    if random.random() < EPSILON:
        return random.choice(actions)  # Explore
    else:
        if state not in q_table:
            q_table[state] = {}
        if not q_table[state]:
            return random.choice(actions)  # If no values, pick random action
        # Exploit: Choose the action with the highest Q-value
        return max(q_table[state], key=q_table[state].get)


# Simulate the crawling and Q-learning process with PDF papers as states
def crawl_and_learn(query):
    visited_papers = set()  # To avoid revisiting the same paper
    to_visit = seed_papers  # Starting point (initial papers)
    state = "start"

    for _ in range(100):  # Limit number of steps (or use another stopping condition)
        print("Iteration ",_)
        # Explore each paper in to_visit
        for url in to_visit:
            if url in visited_papers:
                continue  # Skip already visited papers

            visited_papers.add(url)

            # Extract PDF content
            content = extract_pdf_content(url)

            # Calculate relevance and authority
            relevance = calculate_relevance(query, content)
            authority = calculate_authority(url)

            # Calculate the reward
            reward = relevance * ALPHA + authority * BETA

            # Choose next state (next paper to visit)
            next_state = url  # Could be a citation link (next paper to explore)
            actions = [next_state]  # Actions = available citations (for simplicity here)

            # Update Q-value
            action = choose_action(state, actions)
            update_q_value(state, action, reward, next_state)

            # Set state to next paper
            state = next_state

            # Optionally, extract outbound citation links here and add them to `to_visit`
            # For simplicity, we can assume there are outbound citations to explore further.
            # to_visit = get_outbound_citations(soup)  # You would implement this

    # After crawling, return the top N results (highest Q-values)
    print(q_table)
    top_results = sorted(q_table[state].items(), key=lambda x: x[1], reverse=True)[:5]
    return top_results


# Example usage: Search for a research paper topic
query = "Hidden Markov Models for Natural Language Processing"
results = crawl_and_learn(query)

# Print the best research papers based on Q-values (relevance + authority)
print("Top research papers:")

for url, q_value in results:
    print(f"Paper URL: {url}, Q-value: {q_value}")
