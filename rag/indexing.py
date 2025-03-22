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
    """Extract and prepare documents from processed data."""
    documents = []

    for i, article in enumerate(data):
        # Get article metadata
        title = article.get('title', '')
        time_published = article.get('time_published', '')
        content = article.get('content', '')
        url = article.get('url', '')

        # Create base metadata
        base_metadata = {
            'article_id': i,
            'title': title,
            'time_published': time_published,
            'source': 'article',
            'url': url,
            'document_type': 'article'
        }

        # Add the full article as a document
        full_article = {
            'content': content,
            'metadata': {
                **base_metadata,
                'chunk_type': 'full_article'
            }
        }
        documents.append(full_article)

        # Extract tables from image metadata if available
        tables = []
        if 'metadata' in article and 'images' in article['metadata']:
            for img_idx, img in enumerate(article['metadata']['images']):
                if img.get('parsed_content') and ('table' in img.get('parsed_content', '').lower() or '|' in img.get('parsed_content', '')):
                    table_content = img.get('parsed_content', '')
                    table_caption = img.get('caption', '')

                    table_doc = {
                        'content': table_content,
                        'metadata': {
                            **base_metadata,
                            'chunk_type': 'table',
                            'image_id': img.get('id', img_idx),
                            'caption': table_caption
                        }
                    }
                    tables.append(table_doc)
                    documents.append(table_doc)

    return documents


def extract_heading(paragraph):
    """Extract heading from a paragraph if it contains bold text (** **)."""
    heading_pattern = r'\*\*(.*?)\*\*'
    match = re.search(heading_pattern, paragraph)

    if match:
        heading = match.group(1).strip()
        # Remove the heading pattern from the paragraph
        cleaned_paragraph = re.sub(
            heading_pattern, '', paragraph, count=1).strip()
        return heading, cleaned_paragraph
    return None, paragraph


def create_chunks(documents):
    """Split documents into chunks based on paragraph and table content."""
    paragraph_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )

    chunks = []

    for doc in documents:
        content = doc['content']
        metadata = doc['metadata']
        chunk_type = metadata.get('chunk_type', '')

        if chunk_type == 'table':
            # Tables are already separate chunks
            chunks.append(doc)
        elif chunk_type == 'full_article':
            # Split article into paragraphs
            paragraphs = re.split(r'\n\n+', content)

            current_heading = None

            for para_idx, paragraph in enumerate(paragraphs):
                # Skip empty paragraphs
                if not paragraph.strip():
                    continue

                # Check if paragraph contains a heading (bold text)
                heading, clean_paragraph = extract_heading(paragraph)

                # Update current heading if found
                if heading:
                    current_heading = heading
                    # If the paragraph only contains the heading, skip to next paragraph
                    if not clean_paragraph:
                        continue
                    paragraph = clean_paragraph

                # Check if paragraph is too long and needs further chunking
                if len(paragraph) > CHUNK_SIZE:
                    para_chunks = paragraph_splitter.split_text(paragraph)

                    for chunk_idx, para_chunk in enumerate(para_chunks):
                        chunk_metadata = metadata.copy()
                        chunk_metadata['chunk_type'] = 'paragraph'
                        chunk_metadata['paragraph_id'] = para_idx
                        chunk_metadata['chunk_id'] = chunk_idx
                        chunk_metadata['is_sub_chunk'] = True

                        # Add heading to metadata if available
                        if current_heading:
                            chunk_metadata['heading'] = current_heading

                        chunk_content = para_chunk

                        # Include heading in first chunk of a paragraph if it has a heading
                        if chunk_idx == 0 and current_heading:
                            chunk_content = f"{current_heading}\n{para_chunk}"

                        chunks.append({
                            'content': chunk_content,
                            'metadata': chunk_metadata
                        })
                else:
                    # Paragraph is small enough to be its own chunk
                    chunk_metadata = metadata.copy()
                    chunk_metadata['chunk_type'] = 'paragraph'
                    chunk_metadata['paragraph_id'] = para_idx
                    chunk_metadata['is_sub_chunk'] = False

                    # Add heading to metadata if available
                    if current_heading:
                        chunk_metadata['heading'] = current_heading

                    # Include heading in the content
                    chunk_content = paragraph
                    if current_heading:
                        chunk_content = f"{current_heading}\n{paragraph}"

                    chunks.append({
                        'content': chunk_content,
                        'metadata': chunk_metadata
                    })

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


def index_dataset(data_path, index_name, save_docs=False, docs_output_path=None):
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
