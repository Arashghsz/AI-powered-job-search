import json
import csv
import argparse
import os
from datetime import datetime
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def load_data(file_path):
    """Load job data from JSON or CSV file."""
    if file_path.endswith('.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return []
    elif file_path.endswith('.csv'):
        try:
            return pd.read_csv(file_path).to_dict('records')
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            return []
    else:
        print(f"Unsupported file format: {file_path}")
        return []

def create_job_texts(jobs):
    """Create text representations of jobs for embedding."""
    return [
        f"Title: {job.get('title', '')}. Company: {job.get('company', '')}. " +
        f"Field: {job.get('field', '')}. Description: {job.get('description', '')}"
        for job in jobs
    ]

def calculate_match_probabilities(model, job_texts, query):
    """
    Calculate match probabilities between job texts and query using sentence transformers.
    
    Args:
        model: Sentence transformer model
        job_texts: List of job text representations
        query: User search query
        
    Returns:
        List of similarity scores (between 0 and 1)
    """
    # Encode the query and job texts
    query_embedding = model.encode([query])[0]
    job_embeddings = model.encode(job_texts)
    
    # Calculate similarities
    similarities = cosine_similarity([query_embedding], job_embeddings)[0]
    
    return similarities

def save_to_csv(jobs, match_probabilities, query, output_file=None):
    """
    Save jobs with match probabilities to CSV file.
    
    Args:
        jobs: List of job dictionaries
        match_probabilities: List of match probabilities
        query: The search query used
        output_file: Output file path (optional)
    
    Returns:
        Path to the saved CSV file
    """
    # Create a DataFrame
    df = pd.DataFrame(jobs)
    
    # Add match probability column
    df[f'match_probability_{query.replace(" ", "_")}'] = match_probabilities
    
    # Sort by match probability in descending order
    df = df.sort_values(by=f'match_probability_{query.replace(" ", "_")}', ascending=False)
    
    # Generate output filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        query_str = query.replace(" ", "_")[:30]
        output_file = f"data/ranked_jobs_{query_str}_{timestamp}.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    
    return output_file

def process_query(query, input_file, output_file=None, model_name='all-MiniLM-L6-v2'):
    """
    Process a search query and rank all jobs by match probability.
    
    Args:
        query: Search query
        input_file: Path to input file (JSON or CSV)
        output_file: Path to output CSV file (optional)
        model_name: Name of the sentence transformer model to use
    
    Returns:
        Path to the saved CSV file
    """
    # Load job data
    jobs = load_data(input_file)
    if not jobs:
        print(f"No jobs loaded from {input_file}")
        return None
    
    print(f"Loaded {len(jobs)} jobs. Calculating match probabilities for: '{query}'")
    
    try:
        # Load sentence transformer model
        print(f"Loading sentence transformer model '{model_name}'...")
        model = SentenceTransformer(model_name)
        
        # Create job texts for embedding
        job_texts = create_job_texts(jobs)
        
        # Calculate match probabilities
        match_probabilities = calculate_match_probabilities(model, job_texts, query)
        
        # Save results to CSV
        output_path = save_to_csv(jobs, match_probabilities, query, output_file)
        
        print(f"Job rankings saved to {output_path}")
        return output_path
        
    except ImportError:
        print("Error: Sentence Transformers not installed.")
        print("To install: pip install sentence-transformers")
        return None

def process_multiple_queries(queries, input_file, output_file=None):
    """
    Process multiple search queries and combine the results.
    
    Args:
        queries: List of search queries
        input_file: Path to input file (JSON or CSV)
        output_file: Path to output CSV file (optional)
    
    Returns:
        Path to the saved CSV file
    """
    # Load job data
    jobs = load_data(input_file)
    if not jobs:
        print(f"No jobs loaded from {input_file}")
        return None
    
    print(f"Loaded {len(jobs)} jobs. Processing {len(queries)} queries...")
    
    try:
        # Load sentence transformer model
        print("Loading sentence transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create job texts for embedding
        job_texts = create_job_texts(jobs)
        
        # Create DataFrame
        df = pd.DataFrame(jobs)
        
        # Process each query and add as a column
        for query in queries:
            print(f"Processing query: '{query}'")
            match_probabilities = calculate_match_probabilities(model, job_texts, query)
            df[f'match_probability_{query.replace(" ", "_")}'] = match_probabilities
        
        # Add an average match probability column
        probability_cols = [col for col in df.columns if col.startswith('match_probability_')]
        df['average_match_probability'] = df[probability_cols].mean(axis=1)
        
        # Sort by average match probability
        df = df.sort_values(by='average_match_probability', ascending=False)
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = f"data/ranked_jobs_multiple_queries_{timestamp}.csv"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        print(f"Job rankings saved to {output_file}")
        return output_file
        
    except ImportError:
        print("Error: Sentence Transformers not installed.")
        print("To install: pip install sentence-transformers")
        return None

def main():
    parser = argparse.ArgumentParser(description='Rank jobs by match probability for a search query')
    parser.add_argument('query', nargs='*', help='Search query or queries (e.g., "AI engineering" "full stack development")')
    parser.add_argument('--file', '-f', default='data/erasmusintern_traineeships_2025-02-27_18-28-26.json', 
                        help='Path to input file with job data (JSON or CSV)')
    parser.add_argument('--output', '-o', help='Path to output CSV file')
    parser.add_argument('--model', '-m', default='all-MiniLM-L6-v2', 
                        help='Name of the sentence transformer model to use')
    args = parser.parse_args()
    
    if not args.query:
        parser.error("At least one search query is required")
    
    if len(args.query) == 1:
        # Process a single query
        process_query(args.query[0], args.file, args.output, args.model)
    else:
        # Process multiple queries
        process_multiple_queries(args.query, args.file, args.output)

if __name__ == "__main__":
    main()
