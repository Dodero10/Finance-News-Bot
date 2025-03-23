#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
import statistics
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter, defaultdict
import argparse
import seaborn as sns
from matplotlib.ticker import MaxNLocator

def load_chunks(file_path):
    """Load chunks from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from {file_path}")
    return chunks

def analyze_token_counts(chunks, output_dir='analysis'):
    """Analyze and display statistics about token counts in chunks.
    
    Tokens are counted by splitting text on whitespace, which approximates
    words in Vietnamese text.
    """
    # Count tokens in each chunk
    token_counts = []
    chunk_type_tokens = defaultdict(list)
    
    for chunk in chunks:
        # Split on whitespace to count tokens
        content = chunk['content']
        tokens = content.split()
        token_count = len(tokens)
        token_counts.append(token_count)
        
        # Track by chunk type
        chunk_type = chunk['metadata'].get('chunk_type', 'unknown')
        chunk_type_tokens[chunk_type].append(token_count)
    
    # Basic statistics
    stats = {
        'count': len(token_counts),
        'min': min(token_counts) if token_counts else 0,
        'max': max(token_counts) if token_counts else 0,
        'mean': statistics.mean(token_counts) if token_counts else 0,
        'median': statistics.median(token_counts) if token_counts else 0,
    }
    
    # Add standard deviation separately with proper error handling
    if len(token_counts) > 1:
        stats['stddev'] = statistics.stdev(token_counts)
    else:
        stats['stddev'] = 0
    
    # Print statistics
    print("\nToken Count Statistics:")
    print(f"Total chunks: {stats['count']}")
    print(f"Min tokens: {stats['min']}")
    print(f"Max tokens: {stats['max']}")
    print(f"Mean tokens: {stats['mean']:.2f}")
    print(f"Median tokens: {stats['median']}")
    print(f"Standard deviation: {stats['stddev']:.2f}")
    
    # Create histogram with better styling
    plt.figure(figsize=(12, 7))
    sns.histplot(token_counts, bins=50, kde=True)
    plt.title('Distribution of Token Counts per Chunk', fontsize=15)
    plt.xlabel('Number of Tokens', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(alpha=0.3)
    
    # Add vertical lines for mean and median
    plt.axvline(x=stats['mean'], color='red', linestyle='--', 
                label=f'Mean: {stats["mean"]:.0f} tokens')
    plt.axvline(x=stats['median'], color='green', linestyle='-.', 
                label=f'Median: {stats["median"]:.0f} tokens')
    plt.legend()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'token_count_histogram.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved token count histogram to {output_path}")
    
    # Plot token counts by chunk type
    if len(chunk_type_tokens) > 1:
        plt.figure(figsize=(14, 8))
        
        # Calculate stats for each type
        type_stats = {}
        for chunk_type, counts in chunk_type_tokens.items():
            if counts:  # Only if we have data
                type_stats[chunk_type] = {
                    'count': len(counts),
                    'mean': statistics.mean(counts),
                    'median': statistics.median(counts)
                }
                sns.kdeplot(counts, label=f'{chunk_type} (mean={type_stats[chunk_type]["mean"]:.0f})')
        
        plt.title('Token Count Distribution by Chunk Type', fontsize=15)
        plt.xlabel('Number of Tokens', fontsize=12)
        plt.ylabel('Density', fontsize=12)
        plt.grid(alpha=0.3)
        plt.legend()
        
        # Save plot
        output_path = os.path.join(output_dir, 'token_count_by_type.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved token count by type plot to {output_path}")
        
        # Print stats by chunk type
        print("\nToken counts by chunk type:")
        for chunk_type, stats in sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"  {chunk_type}: {stats['count']} chunks, mean: {stats['mean']:.2f}, median: {stats['median']}")
    
    # Create boxplot to show distribution by type
    if len(chunk_type_tokens) > 1:
        plt.figure(figsize=(14, 8))
        data = []
        labels = []
        
        for chunk_type, counts in chunk_type_tokens.items():
            if len(counts) > 0:  # Only include types with data
                data.append(counts)
                labels.append(f"{chunk_type} (n={len(counts)})")
        
        plt.boxplot(data, labels=labels, showfliers=True)
        plt.title('Token Count Distribution by Chunk Type', fontsize=15)
        plt.xlabel('Chunk Type', fontsize=12)
        plt.ylabel('Number of Tokens', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        
        # Save plot
        output_path = os.path.join(output_dir, 'token_count_boxplot.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved token count boxplot to {output_path}")
    
    # Calculate token density (tokens per character)
    token_densities = []
    for i, chunk in enumerate(chunks):
        content = chunk['content']
        if len(content) > 0:
            density = token_counts[i] / len(content)
            token_densities.append(density)
    
    if token_densities:
        mean_density = statistics.mean(token_densities)
        print(f"\nMean token density: {mean_density:.4f} tokens per character")
        print(f"Mean characters per token: {1/mean_density:.2f}")
    
    # Find chunks with extremely high or low token counts
    try:
        if token_counts and len(token_counts) > 1:
            # Calculate standard deviation directly to avoid KeyError
            stddev = statistics.stdev(token_counts) 
            mean = stats['mean']
            
            if stddev > 0:
                # Define thresholds based on percentiles
                low_threshold = mean - 2 * stddev
                high_threshold = mean + 2 * stddev
                
                low_count_chunks = [i for i, count in enumerate(token_counts) if count < max(1, low_threshold)]
                high_count_chunks = [i for i, count in enumerate(token_counts) if count > high_threshold]
                
                if low_count_chunks:
                    print(f"\nChunks with unusually low token counts (<{max(1, int(low_threshold))}): {len(low_count_chunks)}")
                    
                if high_count_chunks:
                    print(f"Chunks with unusually high token counts (>{int(high_threshold)}): {len(high_count_chunks)}")
    except Exception as e:
        print(f"Warning: Could not analyze token count outliers: {str(e)}")
    
    return stats, token_counts

def analyze_chunk_lengths(chunks, output_dir='analysis'):
    """Analyze and display statistics about chunk lengths."""
    lengths = [len(chunk['content']) for chunk in chunks]
    
    # Basic statistics
    stats = {
        'count': len(lengths),
        'min': min(lengths),
        'max': max(lengths),
        'mean': statistics.mean(lengths),
        'median': statistics.median(lengths),
        'stddev': statistics.stdev(lengths) if len(lengths) > 1 else 0
    }
    
    # Print statistics
    print("\nChunk Length Statistics:")
    print(f"Count: {stats['count']}")
    print(f"Min length: {stats['min']} characters")
    print(f"Max length: {stats['max']} characters")
    print(f"Mean length: {stats['mean']:.2f} characters")
    print(f"Median length: {stats['median']} characters")
    print(f"Standard deviation: {stats['stddev']:.2f} characters")
    
    # Create histogram with better styling
    plt.figure(figsize=(12, 7))
    sns.histplot(lengths, bins=50, kde=True)
    plt.title('Distribution of Chunk Lengths', fontsize=15)
    plt.xlabel('Chunk Length (characters)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(alpha=0.3)
    
    # Add vertical lines for mean and median
    plt.axvline(x=stats['mean'], color='red', linestyle='--', 
                label=f'Mean: {stats["mean"]:.0f} chars')
    plt.axvline(x=stats['median'], color='green', linestyle='-.', 
                label=f'Median: {stats["median"]:.0f} chars')
    plt.legend()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'chunk_length_histogram.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved chunk length histogram to {output_path}")
    
    # Create chunk length distribution by type if chunk_type exists
    chunk_type_lengths = defaultdict(list)
    for chunk in chunks:
        chunk_type = chunk['metadata'].get('chunk_type', 'unknown')
        chunk_type_lengths[chunk_type].append(len(chunk['content']))
    
    if len(chunk_type_lengths) > 1:
        plt.figure(figsize=(14, 8))
        for chunk_type, lengths in chunk_type_lengths.items():
            if lengths:  # Only plot if there are lengths for this type
                sns.kdeplot(lengths, label=f'{chunk_type} (mean={statistics.mean(lengths):.0f})')
        
        plt.title('Chunk Length Distribution by Type', fontsize=15)
        plt.xlabel('Chunk Length (characters)', fontsize=12)
        plt.ylabel('Density', fontsize=12)
        plt.grid(alpha=0.3)
        plt.legend()
        
        # Save plot
        output_path = os.path.join(output_dir, 'chunk_length_by_type.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved chunk length by type plot to {output_path}")
    
    return stats

def analyze_chunk_types(chunks, output_dir='analysis'):
    """Analyze the distribution of chunk types."""
    chunk_types = [chunk['metadata'].get('chunk_type', 'unknown') for chunk in chunks]
    type_counter = Counter(chunk_types)
    
    # Print chunk type distribution
    print("\nChunk Type Distribution:")
    for chunk_type, count in sorted(type_counter.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(chunks)) * 100
        print(f"{chunk_type}: {count} chunks ({percentage:.1f}%)")
    
    # Create pie chart of chunk types with better styling
    if len(type_counter) > 0:
        plt.figure(figsize=(12, 8))
        
        # Create explode effect for the largest segment
        explode = [0.1 if count == max(type_counter.values()) else 0 for count in type_counter.values()]
        
        wedges, texts, autotexts = plt.pie(
            type_counter.values(), 
            labels=type_counter.keys(), 
            autopct='%1.1f%%',
            shadow=True, 
            startangle=90,
            explode=explode,
            textprops={'fontsize': 12}
        )
        
        # Enhance text visibility
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            
        plt.axis('equal')
        plt.title('Chunk Type Distribution', fontsize=15)
        
        # Save plot
        output_path = os.path.join(output_dir, 'chunk_type_distribution.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved chunk type distribution chart to {output_path}")
    
    # Analyze sub-chunks distribution
    sub_chunks = [chunk for chunk in chunks if chunk['metadata'].get('is_sub_chunk', False)]
    print(f"\nSub-chunks: {len(sub_chunks)} ({len(sub_chunks)/len(chunks)*100:.1f}% of total)")
    
    return type_counter

def analyze_metadata_fields(chunks, output_dir='analysis'):
    """Analyze the available metadata fields and their coverage."""
    metadata_fields = defaultdict(int)
    field_values = defaultdict(list)
    
    for chunk in chunks:
        for field, value in chunk['metadata'].items():
            metadata_fields[field] += 1
            # Collect unique values for categorical fields
            if isinstance(value, (str, int, bool)) and field not in ['content', 'title']:
                field_values[field].append(value)
    
    print("\nMetadata Field Coverage:")
    for field, count in sorted(metadata_fields.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(chunks)) * 100
        print(f"{field}: present in {count} chunks ({percentage:.1f}%)")
    
    # Analyze selected categorical fields with reasonable cardinality
    for field, values in field_values.items():
        value_counts = Counter(values)
        # Only show distribution for fields with reasonable cardinality
        if 2 <= len(value_counts) <= 15:
            print(f"\n{field} value distribution:")
            for value, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(values)) * 100
                print(f"  {value}: {count} ({percentage:.1f}%)")
            
            # Create bar chart for this field
            plt.figure(figsize=(10, 6))
            plt.bar(
                [str(k) for k in value_counts.keys()], 
                value_counts.values(), 
                color=sns.color_palette("husl", len(value_counts))
            )
            plt.title(f'Distribution of {field} Values', fontsize=15)
            plt.xlabel(field, fontsize=12)
            plt.ylabel('Count', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', alpha=0.3)
            
            # Adjust layout and save
            plt.tight_layout()
            output_path = os.path.join(output_dir, f'metadata_{field}_distribution.png')
            plt.savefig(output_path, dpi=300)
            print(f"Saved {field} distribution chart to {output_path}")
    
    return metadata_fields

def analyze_paragraph_combinations(chunks, output_dir='analysis'):
    """Analyze how paragraphs were combined in the chunking process."""
    # Count newlines to estimate number of original paragraphs in each chunk
    paragraph_counts = []
    for chunk in chunks:
        content = chunk['content']
        # Count double newlines which typically separate paragraphs
        paragraph_count = content.count('\n\n') + 1
        paragraph_counts.append(paragraph_count)
    
    # Calculate stats
    multi_para_chunks = sum(1 for count in paragraph_counts if count > 1)
    percentage = (multi_para_chunks / len(chunks)) * 100 if chunks else 0
    
    print("\nParagraph Combination Analysis:")
    print(f"Chunks with multiple paragraphs: {multi_para_chunks} ({percentage:.1f}% of total)")
    
    # Create histogram of paragraph counts
    if paragraph_counts:
        plt.figure(figsize=(10, 6))
        bins = max(10, min(30, max(paragraph_counts)))
        
        plt.hist(paragraph_counts, bins=bins, edgecolor='black', alpha=0.7)
        plt.title('Number of Paragraphs per Chunk', fontsize=15)
        plt.xlabel('Paragraph Count', fontsize=12)
        plt.ylabel('Number of Chunks', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        
        # Force integer x-axis
        ax = plt.gca()
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Save plot
        output_path = os.path.join(output_dir, 'paragraphs_per_chunk.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved paragraphs per chunk histogram to {output_path}")
    
    return paragraph_counts

def analyze_image_markers(chunks, output_dir='analysis'):
    """Analyze how [Image] markers are preserved in the chunks."""
    image_marker_pattern = r'\[Image\]'
    
    # Count chunks with image markers
    chunks_with_images = 0
    image_marker_counts = []
    
    for chunk in chunks:
        content = chunk['content']
        count = len(re.findall(image_marker_pattern, content))
        if count > 0:
            chunks_with_images += 1
            image_marker_counts.append(count)
    
    image_percentage = (chunks_with_images / len(chunks)) * 100 if chunks else 0
    
    print("\nImage Marker Analysis:")
    print(f"Chunks containing [Image] markers: {chunks_with_images} ({image_percentage:.1f}% of total)")
    
    if image_marker_counts:
        avg_markers = sum(image_marker_counts) / len(image_marker_counts)
        print(f"Average number of image markers per chunk (when present): {avg_markers:.2f}")
        
        # Create a bar chart of image marker distribution
        counter = Counter(image_marker_counts)
        
        plt.figure(figsize=(10, 6))
        plt.bar(counter.keys(), counter.values(), color='skyblue', edgecolor='black')
        plt.title('Distribution of [Image] Markers per Chunk', fontsize=15)
        plt.xlabel('Number of [Image] Markers', fontsize=12)
        plt.ylabel('Number of Chunks', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        
        # Force integer x-axis
        ax = plt.gca()
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Save plot
        output_path = os.path.join(output_dir, 'image_markers_distribution.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved image markers distribution to {output_path}")
    
    return chunks_with_images, image_marker_counts

def analyze_vietnamese_specific(chunks, output_dir='analysis'):
    """Analyze Vietnamese-specific characteristics in the chunks."""
    # Count Vietnamese diacritical marks to verify Vietnamese text is preserved
    vietnamese_chars = r'[ăâêôơưđÀÁẢÃẠÈÉẺẼẸÌÍỈĨỊÒÓỎÕỌÙÚỦŨỤỲÝỶỸỴàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]'
    
    vn_char_counts = []
    vn_char_densities = []  # Vietnamese chars per total chars
    
    for chunk in chunks:
        content = chunk['content']
        vn_chars = len(re.findall(vietnamese_chars, content))
        total_chars = len(content)
        
        if total_chars > 0:
            vn_char_counts.append(vn_chars)
            vn_char_densities.append(vn_chars / total_chars)
    
    print("\nVietnamese Text Analysis:")
    if vn_char_counts:
        avg_vn_chars = sum(vn_char_counts) / len(vn_char_counts)
        avg_density = sum(vn_char_densities) / len(vn_char_densities)
        print(f"Average Vietnamese characters per chunk: {avg_vn_chars:.2f}")
        print(f"Average Vietnamese character density: {avg_density:.2%}")
        
        # Plot the density distribution
        plt.figure(figsize=(10, 6))
        plt.hist(vn_char_densities, bins=20, edgecolor='black', alpha=0.7)
        plt.title('Distribution of Vietnamese Character Density', fontsize=15)
        plt.xlabel('Vietnamese Character Density (proportion of total)', fontsize=12)
        plt.ylabel('Number of Chunks', fontsize=12)
        plt.grid(alpha=0.3)
        
        # Save plot
        output_path = os.path.join(output_dir, 'vietnamese_char_density.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved Vietnamese character density plot to {output_path}")
    
    # Check for numerical content preservation
    number_pattern = r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)'
    chunks_with_numbers = 0
    
    for chunk in chunks:
        if re.search(number_pattern, chunk['content']):
            chunks_with_numbers += 1
    
    number_percentage = (chunks_with_numbers / len(chunks)) * 100 if chunks else 0
    print(f"Chunks containing numerical values: {chunks_with_numbers} ({number_percentage:.1f}% of total)")
    
    return vn_char_densities

def analyze_semantic_boundaries(chunks, output_dir='analysis'):
    """Analyze whether chunks respect sentence and semantic boundaries."""
    # Check for chunks ending with sentence-breaking punctuation
    sentence_end_pattern = r'[.!?:]$'
    chunks_with_proper_end = 0
    
    for chunk in chunks:
        content = chunk['content'].strip()
        if re.search(sentence_end_pattern, content):
            chunks_with_proper_end += 1
    
    proper_end_percentage = (chunks_with_proper_end / len(chunks)) * 100 if chunks else 0
    
    print("\nSemantic Boundary Analysis:")
    print(f"Chunks ending with proper sentence punctuation: {chunks_with_proper_end} ({proper_end_percentage:.1f}% of total)")
    
    # Check first and last words of chunks to identify potential mid-sentence splits
    suspicious_chunk_starts = []
    suspicious_starts = ['và', 'hoặc', 'nhưng', 'nếu', 'tuy', 'tại', 'do', 'vì', 'bởi', 'cũng', 'nên', 'mà', 'thì']
    
    for i, chunk in enumerate(chunks):
        if chunk['metadata'].get('is_sub_chunk', False):
            first_word = chunk['content'].strip().split(' ')[0].lower()
            if first_word in suspicious_starts:
                suspicious_chunk_starts.append(i)
    
    suspicious_percentage = (len(suspicious_chunk_starts) / len(chunks)) * 100 if chunks else 0
    print(f"Chunks starting with conjunctions/connecting words: {len(suspicious_chunk_starts)} ({suspicious_percentage:.1f}% of total)")
    
    if suspicious_chunk_starts and len(suspicious_chunk_starts) < 10:
        print("Examples of chunks starting with conjunctions:")
        for i in suspicious_chunk_starts[:5]:
            content = chunks[i]['content']
            print(f"  Chunk {i}: {content[:50]}...")
    
    return proper_end_percentage, suspicious_percentage

def analyze_sample_chunks(chunks, num_samples=5):
    """Display sample chunks for manual inspection."""
    if not chunks:
        return
    
    print("\nSample Chunk Analysis:")
    
    # Sample different types of chunks
    chunk_types = set(chunk['metadata'].get('chunk_type', 'unknown') for chunk in chunks)
    
    for chunk_type in chunk_types:
        type_chunks = [c for c in chunks if c['metadata'].get('chunk_type', 'unknown') == chunk_type]
        if not type_chunks:
            continue
            
        print(f"\n{chunk_type.upper()} CHUNK SAMPLES:")
        
        # Get some short and some long examples
        type_chunks.sort(key=lambda x: len(x['content']))
        sample_indices = [0]  # shortest
        
        if len(type_chunks) > 1:
            sample_indices.append(len(type_chunks) - 1)  # longest
        
        # Add some random samples from the middle
        import random
        if len(type_chunks) > 2:
            middle_indices = list(range(1, len(type_chunks) - 1))
            samples_to_take = min(num_samples - len(sample_indices), len(middle_indices))
            if samples_to_take > 0:
                sample_indices.extend(random.sample(middle_indices, samples_to_take))
        
        # Print the samples
        for i, idx in enumerate(sample_indices):
            chunk = type_chunks[idx]
            content = chunk['content']
            
            # Truncate very long content for display
            if len(content) > 300:
                display_content = content[:300] + "..."
            else:
                display_content = content
                
            print(f"\nSample {i+1} (length: {len(content)} chars):")
            print(f"Content: {display_content}")
            
            # Print key metadata
            print("Key metadata:")
            for key in ['paragraph_id', 'is_sub_chunk', 'heading', 'chunk_id']:
                if key in chunk['metadata']:
                    print(f"  {key}: {chunk['metadata'][key]}")

def main():
    """Analyze chunks saved from the RAG system."""
    parser = argparse.ArgumentParser(description='Analyze RAG chunks')
    parser.add_argument('--file', '-f', type=str, required=True, 
                        help='Path to the JSON file containing chunks')
    parser.add_argument('--output', '-o', type=str, default='analysis', 
                        help='Directory to save analysis results')
    parser.add_argument('--samples', '-s', type=int, default=5,
                        help='Number of sample chunks to display for each type')
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load chunks
    try:
        chunks = load_chunks(args.file)
    except Exception as e:
        print(f"Error loading chunks: {str(e)}")
        return
    
    if not chunks:
        print("No chunks found in the file.")
        return
    
    # Perform comprehensive analyses
    # Wrap each analysis in its own try/except to continue if one fails
    try:
        # Add token count analysis first
        analyze_token_counts(chunks, args.output)
    except Exception as e:
        print(f"Error during token count analysis: {str(e)}")
        
    try:
        analyze_chunk_lengths(chunks, args.output)
    except Exception as e:
        print(f"Error during chunk length analysis: {str(e)}")
        
    try:
        analyze_chunk_types(chunks, args.output)
    except Exception as e:
        print(f"Error during chunk type analysis: {str(e)}")
        
    try:
        analyze_metadata_fields(chunks, args.output)
    except Exception as e:
        print(f"Error during metadata field analysis: {str(e)}")
        
    try:
        analyze_paragraph_combinations(chunks, args.output)
    except Exception as e:
        print(f"Error during paragraph combination analysis: {str(e)}")
        
    try:
        analyze_image_markers(chunks, args.output)
    except Exception as e:
        print(f"Error during image marker analysis: {str(e)}")
        
    try:
        analyze_vietnamese_specific(chunks, args.output)
    except Exception as e:
        print(f"Error during Vietnamese-specific analysis: {str(e)}")
        
    try:
        analyze_semantic_boundaries(chunks, args.output)
    except Exception as e:
        print(f"Error during semantic boundary analysis: {str(e)}")
        
    try:
        analyze_sample_chunks(chunks, args.samples)
    except Exception as e:
        print(f"Error during sample chunk analysis: {str(e)}")
    
    # Create an HTML report with all the images
    try:
        create_html_report(args.file, args.output)
    except Exception as e:
        print(f"Error creating HTML report: {str(e)}")
    
    print(f"\nAnalysis completed! Results saved to {args.output}/")

def create_html_report(input_file, output_dir):
    """Create an HTML report with all the images and analysis summary."""
    # Get all image files in the output directory
    image_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
    
    if not image_files:
        return
    
    # Import datetime here to avoid issues
    import datetime
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chunk Analysis Report - {os.path.basename(input_file)}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #2c3e50; }}
            .image-container {{ margin: 20px 0; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }}
            img {{ max-width: 100%; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 0.8em; color: #7f8c8d; }}
        </style>
    </head>
    <body>
        <h1>Chunk Analysis Report</h1>
        <p>Source file: <strong>{input_file}</strong></p>
        <p>Generated on: <strong>{current_time}</strong></p>
        
        <h2>Analysis Results</h2>
    """
    
    # Add each image to the report
    for image_file in sorted(image_files):
        image_name = image_file.replace('_', ' ').replace('.png', '')
        html_content += f"""
        <div class="image-container">
            <h3>{image_name.title()}</h3>
            <img src="{image_file}" alt="{image_name}">
        </div>
        """
    
    html_content += """
        <div class="footer">
            <p>Generated by the RAG Chunk Analyzer</p>
        </div>
    </body>
    </html>
    """
    
    # Write the HTML file
    html_path = os.path.join(output_dir, 'chunk_analysis_report.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Created HTML report: {html_path}")

if __name__ == "__main__":
    main() 