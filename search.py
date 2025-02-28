import json
import argparse
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def load_job_data(file_path):
    """Load job data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}.")
        return []

def create_job_texts(jobs):
    """Create text representations of jobs for embedding."""
    return [
        f"Title: {job.get('title', '')}. Company: {job.get('company', '')}. " +
        f"Field: {job.get('field', '')}. Description: {job.get('description', '')}"
        for job in jobs
    ]

def semantic_search(model, job_texts, jobs, query, top_n=10):
    """
    Use sentence transformers to perform semantic search on job listings.
    
    Args:
        model: Sentence transformer model
        job_texts: List of job text representations
        jobs: List of job dictionaries
        query: User search query
        top_n: Number of top results to return
        
    Returns:
        List of relevant job listings
    """
    # Encode the query and job texts
    query_embedding = model.encode([query])[0]
    job_embeddings = model.encode(job_texts)
    
    # Calculate similarities
    similarities = cosine_similarity([query_embedding], job_embeddings)[0]
    
    # Get indices of top-n most similar jobs
    top_indices = np.argsort(similarities)[::-1][:top_n]
    
    # Return the relevant jobs
    return [(jobs[i], similarities[i]) for i in top_indices]

def format_job(job, similarity=None):
    """Format a job listing for display."""
    similarity_str = f"MATCH SCORE: {similarity:.2f}" if similarity is not None else ""
    return f"""
{'-' * 80}
TITLE: {job.get('title', 'N/A')}
COMPANY: {job.get('company', 'N/A')}
LOCATION: {job.get('location', 'N/A')}
FIELD: {job.get('field', 'N/A')}
DURATION: {job.get('duration', 'N/A')}
POSTED: {job.get('post_date', 'N/A')}
DEADLINE: {job.get('deadline', 'N/A')}
URL: {job.get('url', 'N/A')}
{similarity_str}

DESCRIPTION:
{job.get('description', 'N/A')}
{'-' * 80}
"""

def keyword_matching(jobs, query_terms):
    """Perform basic keyword matching as a fallback."""
    matches = []
    query_terms = [term.lower() for term in query_terms]
    
    for job in jobs:
        score = 0
        job_text = (
            job.get('title', '').lower() + ' ' +
            job.get('company', '').lower() + ' ' +
            job.get('field', '').lower() + ' ' +
            job.get('description', '').lower()
        )
        
        for term in query_terms:
            if term in job_text:
                score += 1
        
        if score > 0:
            matches.append((job, score / len(query_terms)))
    
    # Sort by score in descending order
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Semantic job search using sentence transformers')
    parser.add_argument('query', help='Search query (e.g., "full-stack development")')
    parser.add_argument('--file', '-f', default='data/erasmusintern_traineeships_2025-02-27_18-28-26.json', help='Path to JSON file with job data')
    parser.add_argument('--results', '-n', type=int, default=5, help='Number of results to return')
    parser.add_argument('--method', '-m', choices=['transformer', 'keyword'], default='transformer',
                      help='Search method to use: transformer (more accurate) or keyword (faster)')
    args = parser.parse_args()
    
    # Load job data
    jobs = load_job_data(args.file)
    if not jobs:
        return
    
    print(f"Loaded {len(jobs)} jobs. Searching for: '{args.query}'")
    
    try:
        if args.method == 'transformer':
            # Load pre-trained sentence transformer model
            print("Loading sentence transformer model (this may take a moment)...")
            model = SentenceTransformer('all-MiniLM-L6-v2')  # Small and fast model
            
            # Prepare job texts
            job_texts = create_job_texts(jobs)
            
            # Perform semantic search
            results = semantic_search(model, job_texts, jobs, args.query, args.results)
        else:
            # Use simpler keyword matching
            print("Using keyword matching...")
            query_terms = args.query.split()
            results = keyword_matching(jobs, query_terms)[:args.results]
    except ImportError:
        print("Sentence Transformers not installed. Falling back to keyword matching.")
        print("To install: pip install sentence-transformers")
        
        # Fall back to keyword matching
        query_terms = args.query.split()
        results = keyword_matching(jobs, query_terms)[:args.results]
    
    # Display results
    if results:
        print(f"\nFound {len(results)} relevant jobs:")
        for job, score in results:
            print(format_job(job, score))
    else:
        print("\nNo relevant jobs found for your query.")
    
    if args.method == 'transformer':
        print("\nNote: For better results, install the sentence-transformers package:")
        print("pip install sentence-transformers")

if __name__ == "__main__":
    main()