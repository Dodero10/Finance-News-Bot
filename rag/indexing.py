import json
import os
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from rag.config import HUGGINGFACE_TOKEN, CHROMA_DB_PATH, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
from langchain_huggingface import HuggingFaceEmbeddings
import logging
import time
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("indexing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rag_indexing")

def prepare_documents(data):
    """
    Convert raw JSON data into document format for further processing.
    
    Args:
        data: List of article dictionaries
    
    Returns:
        List of document dictionaries with content and metadata
    """
    documents = []
    for i, article in enumerate(data):
        document = {
            'content': article.get('content', ''),
            'metadata': {
                'article_id': i,
                'title': article.get('title', ''),
                'time_published': article.get('time_published', ''),
                'source': 'article',
                'url': article.get('url', ''),
                'document_type': 'article',
                'images': article.get('metadata', {}).get('images', [])
            }
        }
        documents.append(document)
    return documents

def vietnamese_sentence_split(text):
    """
    Split Vietnamese text into sentences with proper handling of special cases.
    
    This function handles Vietnamese sentence boundaries better than NLTK's
    sent_tokenize for Vietnamese text.
    
    Args:
        text: Vietnamese text to split into sentences
        
    Returns:
        List of sentences
    """
    # Pattern captures complete sentences ending with: . ! ? ...
    # Accounts for periods in numbers, abbreviations and special cases
    pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!|\…)(?=\s|[A-Z]|$)|\n\n'
    
    # For Vietnamese text specifically, use a pattern that handles:
    # - Normal punctuation: . ! ?
    # - Vietnamese quotation marks: " " ' '
    # - Ellipsis: ...
    # - But doesn't split on abbreviations or numbers: TS., PGS., 1.5, etc.
    sentences = []
    
    # First split by paragraph breaks to preserve them as context boundaries
    paragraphs = re.split(r'\n\n+', text)
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        # Split paragraph using regex while preserving sentence-ending punctuation
        splits = re.split(r'([.!?]["|"|\'|\']*\s+)', paragraph)
        
        # Recombine the splits to get complete sentences with punctuation
        current_sentence = ""
        for i in range(0, len(splits), 2):
            if i < len(splits):
                current_sentence += splits[i]
                
            if i + 1 < len(splits):
                current_sentence += splits[i + 1]
                sentences.append(current_sentence.strip())
                current_sentence = ""
                
        # Add the last part if any remains
        if current_sentence:
            sentences.append(current_sentence.strip())
    
    # For paragraphs that might not have sentence-ending punctuation
    if not sentences and text.strip():
        sentences = [text.strip()]
        
    return sentences

def is_heading(text):
    """Check if text is a heading (e.g., bold text or short standalone phrase)."""
    # Check for markdown-style headings (**heading**)
    if re.match(r'^\s*\*\*.*\*\*\s*$', text):
        return True
    
    # Check for short all-uppercase phrases which are likely headings
    if re.match(r'^\s*[A-Z\dĂÂÊÔƠƯĐăâêôơưđÀÁẢÃẠÈÉẺẼẸÌÍỈĨỊÒÓỎÕỌÙÚỦŨỤỲÝỶỸỴàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ\s]{5,50}\s*$', text) and len(text) < 60:
        return True
    
    return False

def create_chunks(documents, max_chunk_size=1000, min_chunk_size=200):
    """
    Create semantically meaningful chunks from documents optimized for Vietnamese text.
    Combine small paragraphs and keep image markers in text.
    
    Args:
        documents: List of document dictionaries
        max_chunk_size: Maximum size of a chunk in characters
        min_chunk_size: Minimum size of a chunk in characters
    
    Returns:
        List of chunk dictionaries with content and metadata
    """
    chunks = []
    
    for doc in documents:
        content = doc['content']
        metadata = doc['metadata'].copy()
        
        # Process tables separately if they exist
        tables = []
        if 'images' in metadata:
            for i, img in enumerate(metadata['images']):
                parsed_content = img.get('parsed_content')
                if parsed_content is not None and isinstance(parsed_content, str) and '|' in parsed_content:
                    table_content = parsed_content
                    if table_content:
                        tables.append({
                            'content': table_content,
                            'metadata': {
                                **metadata,
                                'chunk_type': 'table',
                                'image_id': img.get('id', i),
                                'caption': img.get('caption', '')
                            }
                        })
        
        # Split content into paragraphs but preserve [Image] markers
        paragraphs = re.split(r'\n\n+', content.strip())
        
        # Process paragraphs and potentially combine small ones
        current_heading = None
        combined_paragraph = ""
        combined_paragraphs = []
        
        for para_id, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Check if this paragraph is a heading
            if is_heading(paragraph):
                current_heading = paragraph.replace('*', '')
                
                # If we have accumulated content, add it as a chunk before starting with new heading
                if combined_paragraph:
                    combined_paragraphs.append({
                        'content': combined_paragraph,
                        'metadata': {
                            'heading': current_heading,
                            'paragraph_ids': list(range(para_id - len(combined_paragraph.split('\n\n')), para_id))
                        }
                    })
                    combined_paragraph = ""
                
                continue
            
            # Key change: Try to combine small paragraphs
            if combined_paragraph and len(combined_paragraph) + len(paragraph) + 4 <= max_chunk_size:
                # 4 accounts for the "\n\n" separator
                combined_paragraph += "\n\n" + paragraph
            else:
                # If we have accumulated content, add it as a chunk
                if combined_paragraph:
                    combined_paragraphs.append({
                        'content': combined_paragraph,
                        'metadata': {
                            'heading': current_heading,
                            'paragraph_ids': list(range(para_id - len(combined_paragraph.split('\n\n')), para_id))
                        }
                    })
                # Start a new combined paragraph
                combined_paragraph = paragraph
        
        # Don't forget the last combined paragraph
        if combined_paragraph:
            combined_paragraphs.append({
                'content': combined_paragraph,
                'metadata': {
                    'heading': current_heading,
                    'paragraph_ids': list(range(len(paragraphs) - len(combined_paragraph.split('\n\n')), len(paragraphs)))
                }
            })
        
        # Process each combined paragraph
        for chunk_id, para_info in enumerate(combined_paragraphs):
            paragraph = para_info['content']
            chunk_heading = para_info['metadata'].get('heading')
            paragraph_ids = para_info['metadata'].get('paragraph_ids', [chunk_id])
            
            # For paragraphs below threshold, keep as is (with image markers intact)
            if len(paragraph) <= max_chunk_size:
                chunks.append({
                    'content': paragraph,
                    'metadata': {
                        **metadata,
                        'chunk_type': 'paragraph',
                        'paragraph_id': paragraph_ids[0] if paragraph_ids else chunk_id,
                        'is_sub_chunk': False,
                        **({"heading": chunk_heading} if chunk_heading else {})
                    }
                })
                continue
            
            # For longer paragraphs, split into semantic chunks
            sentences = vietnamese_sentence_split(paragraph)
            
            if not sentences:
                continue
                
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                # Preserve [Image] markers in sentences
                sentence_length = len(sentence)
                
                # If adding this sentence exceeds max_chunk_size and we have enough content,
                # create a chunk and start a new one
                if current_length + sentence_length > max_chunk_size and current_length >= min_chunk_size:
                    chunk_text = " ".join(current_chunk)
                    chunks.append({
                        'content': chunk_text,
                        'metadata': {
                            **metadata,
                            'chunk_type': 'paragraph',
                            'paragraph_id': paragraph_ids[0] if paragraph_ids else chunk_id,
                            'is_sub_chunk': True,
                            **({"heading": chunk_heading} if chunk_heading else {})
                        }
                    })
                    current_chunk = []
                    current_length = 0
                
                # Handle very long sentences
                if sentence_length > max_chunk_size:
                    # If we have accumulated content, save it first
                    if current_chunk:
                        chunk_text = " ".join(current_chunk)
                        chunks.append({
                            'content': chunk_text,
                            'metadata': {
                                **metadata,
                                'chunk_type': 'paragraph',
                                'paragraph_id': paragraph_ids[0] if paragraph_ids else chunk_id,
                                'is_sub_chunk': True,
                                **({"heading": chunk_heading} if chunk_heading else {})
                            }
                        })
                        current_chunk = []
                        current_length = 0
                    
                    # Split the long sentence by phrases
                    phrase_parts = re.split(r'(,|;|:|–|-)', sentence)
                    current_phrase = ""
                    
                    for i in range(0, len(phrase_parts), 2):
                        if i < len(phrase_parts):
                            part = phrase_parts[i]
                            
                            if len(current_phrase) + len(part) > max_chunk_size and current_phrase:
                                chunks.append({
                                    'content': current_phrase,
                                    'metadata': {
                                        **metadata,
                                        'chunk_type': 'paragraph',
                                        'paragraph_id': paragraph_ids[0] if paragraph_ids else chunk_id,
                                        'is_sub_chunk': True,
                                        **({"heading": chunk_heading} if chunk_heading else {})
                                    }
                                })
                                current_phrase = part
                            else:
                                current_phrase += part
                                
                            # Add the separator back
                            if i + 1 < len(phrase_parts):
                                current_phrase += phrase_parts[i + 1]
                    
                    if current_phrase:
                        chunks.append({
                            'content': current_phrase,
                            'metadata': {
                                **metadata,
                                'chunk_type': 'paragraph',
                                'paragraph_id': paragraph_ids[0] if paragraph_ids else chunk_id,
                                'is_sub_chunk': True,
                                **({"heading": chunk_heading} if chunk_heading else {})
                            }
                        })
                else:
                    # Normal case: add sentence to current chunk
                    current_chunk.append(sentence)
                    current_length += sentence_length
            
            # Don't forget the last chunk
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'metadata': {
                        **metadata,
                        'chunk_type': 'paragraph',
                        'paragraph_id': paragraph_ids[0] if paragraph_ids else chunk_id,
                        'is_sub_chunk': len(current_chunk) < len(sentences),
                        **({"heading": chunk_heading} if chunk_heading else {})
                    }
                })
        
        # Add the tables
        chunks.extend(tables)
    
    # Consistently assign chunk IDs to sub-chunks
    chunk_id_counter = 0
    for chunk in chunks:
        if chunk['metadata'].get('is_sub_chunk', False):
            chunk['metadata']['chunk_id'] = chunk_id_counter
            chunk_id_counter += 1
    
    return chunks

def create_vector_index(chunks, index_name="default"):
    """Create a vector index from chunks with progress tracking."""
    # Create directory if it doesn't exist
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    
    logger.info(f"Initializing embedding model: {EMBEDDING_MODEL}")
    try:
        # Initialize embedding model
        embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={
                'device': 'cpu',
                'token': HUGGINGFACE_TOKEN
            },
            encode_kwargs={'normalize_embeddings': True}
        )
        
        logger.info("Embedding model initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing embedding model: {str(e)}")
        raise
    
    # Create and persist Chroma DB
    logger.info("Extracting texts and metadata from chunks...")
    texts = [chunk['content'] for chunk in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]
    
    # Log sample of first chunk
    if len(chunks) > 0:
        logger.info(f"Sample chunk: {texts[0][:100]}...")
        logger.info(f"Sample metadata: {metadatas[0]}")
    
    logger.info(f"Creating Chroma collection: {index_name}")
    
    batch_size = 100  # Process in batches to show progress
    total_batches = (len(texts) + batch_size - 1) // batch_size
    
    all_ids = []
    
    try:
        # Create empty collection first
        db = Chroma(
            embedding_function=embedding_model,
            persist_directory=CHROMA_DB_PATH,
            collection_name=index_name
        )
        
        # Add documents in batches with progress tracking
        logger.info(f"Adding {len(texts)} documents in {total_batches} batches")
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Indexing progress"):
            batch_end = min(i + batch_size, len(texts))
            batch_texts = texts[i:batch_end]
            batch_metadatas = metadatas[i:batch_end]
            
            # Add batch to collection
            ids = db.add_texts(
                texts=batch_texts,
                metadatas=batch_metadatas
            )
            all_ids.extend(ids)
            
            # Log progress
            if (i // batch_size) % 5 == 0 or batch_end == len(texts):
                logger.info(f"Processed {batch_end}/{len(texts)} documents")
        
        # Persist to disk
        logger.info("Persisting Chroma DB to disk...")
        db.persist()
        logger.info(f"Chroma DB persisted with {len(all_ids)} documents")
        
        return db
    except Exception as e:
        logger.error(f"Error creating vector index: {str(e)}")
        raise


def index_dataset(data_path, index_name, save_docs=False, docs_output_path=None, save_chunks_flag=False, chunks_output_path=None):
    """Index a dataset from JSON file with detailed logging."""
    start_time = time.time()
    logger.info(f"Starting indexing for dataset: {index_name}")
    logger.info(f"Loading data from {data_path}...")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} articles")
    
    logger.info("Preparing documents...")
    documents = prepare_documents(data)
    logger.info(f"Prepared {len(documents)} documents")
    
    # Log document types count
    doc_types = {}
    for doc in documents:
        chunk_type = doc['metadata'].get('chunk_type', 'unknown')
        doc_types[chunk_type] = doc_types.get(chunk_type, 0) + 1
    
    logger.info(f"Document types distribution: {doc_types}")
    
    # Save prepared documents if requested
    if save_docs:
        if not docs_output_path:
            base_name = os.path.basename(data_path).split('.')[0]
            docs_output_path = f"prepared_docs/{base_name}_prepared.json"
        logger.info(f"Saving prepared documents to {docs_output_path}")
        save_prepared_documents(documents, docs_output_path)
    
    logger.info("Creating chunks...")
    chunk_start = time.time()
    chunks = create_chunks(documents)
    logger.info(f"Created {len(chunks)} chunks in {time.time() - chunk_start:.2f} seconds")
    
    # Log chunk types
    chunk_types = {}
    for chunk in chunks:
        chunk_type = chunk['metadata'].get('chunk_type', 'unknown')
        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
    
    logger.info(f"Chunk types distribution: {chunk_types}")
    
    # Save chunks before embedding if requested
    if save_chunks_flag:
        if not chunks_output_path:
            base_name = os.path.basename(data_path).split('.')[0]
            chunks_output_path = f"chunks/{base_name}_chunks.json"
        logger.info(f"Saving chunks before embedding to {chunks_output_path}")
        save_chunks(chunks, chunks_output_path)
    
    logger.info(f"Creating vector index '{index_name}'...")
    embedding_start = time.time()
    
    # Add progress bar for embedding creation
    logger.info("Generating embeddings for chunks (this may take a while)...")
    
    db = create_vector_index(chunks, index_name)
    
    logger.info(f"Vector index created in {time.time() - embedding_start:.2f} seconds")
    logger.info(f"Successfully created vector index with {len(chunks)} chunks")
    logger.info(f"Total indexing time: {time.time() - start_time:.2f} seconds")
    
    return db


def save_prepared_documents(documents, output_path):
    """Save prepared documents to a JSON file."""
    output_dir = os.path.dirname(output_path)
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert documents to a serializable format
    serializable_docs = []
    for doc in documents:
        serializable_doc = {
            'content': doc['content'],
            'metadata': doc['metadata']
        }
        serializable_docs.append(serializable_doc)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_docs, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(documents)} prepared documents to {output_path}")
    return output_path

def save_chunks(chunks, output_path):
    """
    Save chunks to JSON file.
    
    Args:
        chunks: List of chunk dictionaries
        output_path: Path to save JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
