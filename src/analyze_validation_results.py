"""
Analysis script for citation validation results.

This script analyzes the citation_validation_results.json file to identify
patterns in errors and mistakes in citation validation.

Usage:
    python src/analyze_validation_results.py [--input FILE]
"""

import json
import os
import logging
import argparse
from collections import Counter, defaultdict
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_error_classifications(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze error classifications across all validation results.
    
    Args:
        results: List of validation result dictionaries
        
    Returns:
        Dictionary with error classification statistics
    """
    error_counts = Counter()
    error_examples = defaultdict(list)
    
    for result in results:
        classifications = result.get('error_classifications', [])
        for error_type in classifications:
            error_counts[error_type] += 1
            
            # Store example for each error type (limit to 5 examples)
            if len(error_examples[error_type]) < 5:
                ref_title = result.get('reference', {}).get('title', 'Unknown')[:100]
                error_examples[error_type].append({
                    'title': ref_title,
                    'mismatches': result.get('mismatches', [])[:3]  # First 3 mismatches
                })
    
    return {
        'counts': dict(error_counts),
        'examples': dict(error_examples)
    }


def analyze_title_similarities(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze title similarity scores to identify potential issues.
    
    Args:
        results: List of validation result dictionaries
        
    Returns:
        Dictionary with title similarity statistics
    """
    similarities = []
    low_similarity_examples = []
    
    for result in results:
        similarity = result.get('title_similarity', 0.0)
        if similarity > 0:
            similarities.append(similarity)
            
            # Collect examples of low similarity matches that were still considered
            if similarity < 95.0 and result.get('validation_status') in ['matched', 'author_mismatch']:
                ref_title = result.get('reference', {}).get('title', 'Unknown')
                dblp_match = result.get('dblp_match')
                dblp_title = dblp_match.get('title', 'Unknown') if dblp_match else 'Unknown'
                if len(low_similarity_examples) < 10:
                    low_similarity_examples.append({
                        'similarity': similarity,
                        'ref_title': ref_title[:100],
                        'dblp_title': dblp_title[:100],
                        'status': result.get('validation_status')
                    })
    
    if not similarities:
        return {'error': 'No title similarities found'}
    
    similarities.sort()
    n = len(similarities)
    
    return {
        'count': n,
        'min': min(similarities),
        'max': max(similarities),
        'mean': sum(similarities) / n,
        'median': similarities[n // 2],
        'p25': similarities[n // 4],
        'p75': similarities[3 * n // 4],
        'low_similarity_examples': low_similarity_examples
    }


def analyze_author_list_lengths(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze differences in author list lengths between references and DBLP.
    
    Args:
        results: List of validation result dictionaries
        
    Returns:
        Dictionary with author list length statistics
    """
    length_diffs = []
    examples = []
    
    for result in results:
        ref_authors = result.get('reference', {}).get('authors', [])
        dblp_match = result.get('dblp_match')
        dblp_authors = dblp_match.get('authors', []) if dblp_match else []
        
        if ref_authors and dblp_authors:
            diff = len(dblp_authors) - len(ref_authors)
            length_diffs.append(diff)
            
            # Collect examples of large differences
            if abs(diff) > 5 and len(examples) < 10:
                examples.append({
                    'ref_count': len(ref_authors),
                    'dblp_count': len(dblp_authors),
                    'diff': diff,
                    'title': result.get('reference', {}).get('title', 'Unknown')[:100],
                    'status': result.get('validation_status', 'unknown')
                })
    
    if not length_diffs:
        return {'error': 'No author list length data found'}
    
    return {
        'count': len(length_diffs),
        'mean_diff': sum(length_diffs) / len(length_diffs),
        'min_diff': min(length_diffs),
        'max_diff': max(length_diffs),
        'positive_diff_count': sum(1 for d in length_diffs if d > 0),
        'negative_diff_count': sum(1 for d in length_diffs if d < 0),
        'zero_diff_count': sum(1 for d in length_diffs if d == 0),
        'examples': examples
    }


def identify_common_mistakes(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify common mistakes in citation validation.
    
    Args:
        results: List of validation result dictionaries
        
    Returns:
        List of common mistake patterns
    """
    mistakes = []
    
    # Mistake 1: Title similarity too low but still matched
    low_sim_matched = []
    for result in results:
        similarity = result.get('title_similarity', 0.0)
        status = result.get('validation_status', '')
        if 80.0 <= similarity < 90.0 and status in ['matched', 'author_mismatch']:
            ref_title = result.get('reference', {}).get('title', '')
            dblp_match = result.get('dblp_match')
            dblp_title = dblp_match.get('title', '') if dblp_match else ''
            low_sim_matched.append({
                'similarity': similarity,
                'status': status,
                'ref_title': ref_title[:100],
                'dblp_title': dblp_title[:100]
            })
    
    if low_sim_matched:
        mistakes.append({
            'type': 'Low title similarity but still processed',
            'count': len(low_sim_matched),
            'description': 'Titles with similarity between 80-90% were still processed',
            'examples': low_sim_matched[:5]
        })
    
    # Mistake 2: Author order issues
    order_issues = []
    for result in results:
        if 'author_order_wrong' in result.get('error_classifications', []):
            dblp_match = result.get('dblp_match')
            dblp_authors = dblp_match.get('authors', [])[:5] if dblp_match else []
            order_issues.append({
                'title': result.get('reference', {}).get('title', '')[:100],
                'ref_authors': result.get('reference', {}).get('authors', [])[:5],
                'dblp_authors': dblp_authors
            })
    
    if order_issues:
        mistakes.append({
            'type': 'Author order mismatches',
            'count': len(order_issues),
            'description': 'Authors match but are in wrong order',
            'examples': order_issues[:5]
        })
    
    # Mistake 3: Accent issues
    accent_issues = []
    for result in results:
        if 'accents_missing' in result.get('error_classifications', []):
            accent_issues.append({
                'title': result.get('reference', {}).get('title', '')[:100],
                'mismatches': result.get('mismatches', [])[:3]
            })
    
    if accent_issues:
        mistakes.append({
            'type': 'Accent/diacritic mismatches',
            'count': len(accent_issues),
            'description': 'Names differ only by accents/diacritics',
            'examples': accent_issues[:5]
        })
    
    # Mistake 4: First/Last name mismatches
    name_mismatches = []
    for result in results:
        classifications = result.get('error_classifications', [])
        if 'first_name_mismatch' in classifications or 'last_name_mismatch' in classifications:
            name_mismatches.append({
                'title': result.get('reference', {}).get('title', '')[:100],
                'classifications': classifications,
                'mismatches': result.get('mismatches', [])[:3]
            })
    
    if name_mismatches:
        mistakes.append({
            'type': 'First/Last name mismatches',
            'count': len(name_mismatches),
            'description': 'Names differ in first or last name components',
            'examples': name_mismatches[:5]
        })
    
    return mistakes


def main():
    """Main function to analyze validation results."""
    parser = argparse.ArgumentParser(
        description='Analyze citation validation results.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--input', type=str, default='citation_validation_results.json',
                       help='Input JSON file with validation results')
    parser.add_argument('--output', type=str, default='validation_analysis.json',
                       help='Output JSON file for analysis results')
    
    args = parser.parse_args()
    
    # Load validation results
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        return
    
    logger.info(f"Loading validation results from: {args.input}")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        return
    
    # Extract all results from all files
    all_results = []
    for file_data in data.get('files', []):
        all_results.extend(file_data.get('results', []))
    
    logger.info(f"Analyzing {len(all_results)} validation results")
    
    # Perform analyses
    analysis = {
        'summary': data.get('summary', {}),
        'error_classifications': analyze_error_classifications(all_results),
        'title_similarities': analyze_title_similarities(all_results),
        'author_list_lengths': analyze_author_list_lengths(all_results),
        'common_mistakes': identify_common_mistakes(all_results)
    }
    
    # Write analysis results
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        logger.info(f"Analysis results written to: {args.output}")
    except Exception as e:
        logger.error(f"Error writing analysis results: {e}")
        return
    
    # Print summary to console
    print("\n" + "="*60)
    print("VALIDATION ANALYSIS SUMMARY")
    print("="*60)
    
    summary = data.get('summary', {})
    print(f"\nOverall Statistics:")
    print(f"  Files processed: {summary.get('files_processed', 0)}")
    print(f"  Total references: {summary.get('total_references', 0)}")
    print(f"  Matched: {summary.get('total_matched', 0)}")
    print(f"  Mismatches: {summary.get('total_mismatches', 0)}")
    print(f"  No match: {summary.get('total_no_match', 0)}")
    print(f"  Errors: {summary.get('total_errors', 0)}")
    
    # Error classifications
    error_class = analysis.get('error_classifications', {})
    if error_class.get('counts'):
        print(f"\nError Classifications:")
        for error_type, count in sorted(error_class['counts'].items(), key=lambda x: -x[1]):
            print(f"  {error_type}: {count}")
    
    # Title similarities
    title_sim = analysis.get('title_similarities', {})
    if 'mean' in title_sim:
        print(f"\nTitle Similarity Statistics:")
        print(f"  Mean: {title_sim['mean']:.2f}%")
        print(f"  Median: {title_sim['median']:.2f}%")
        print(f"  Min: {title_sim['min']:.2f}%")
        print(f"  Max: {title_sim['max']:.2f}%")
    
    # Author list lengths
    author_lengths = analysis.get('author_list_lengths', {})
    if 'mean_diff' in author_lengths:
        print(f"\nAuthor List Length Differences:")
        print(f"  Mean difference (DBLP - Reference): {author_lengths['mean_diff']:.2f}")
        print(f"  Cases where DBLP has more authors: {author_lengths['positive_diff_count']}")
        print(f"  Cases where Reference has more authors: {author_lengths['negative_diff_count']}")
        print(f"  Cases with same length: {author_lengths['zero_diff_count']}")
    
    # Common mistakes
    mistakes = analysis.get('common_mistakes', [])
    if mistakes:
        print(f"\nCommon Mistakes Identified:")
        for mistake in mistakes:
            print(f"  {mistake['type']}: {mistake['count']} cases")
            print(f"    {mistake['description']}")
    
    print("\n" + "="*60)
    print(f"Full analysis saved to: {args.output}")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
