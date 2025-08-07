import json
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
import logging

CRAWLED_DATA = "../data/crawled_data_20250806_122427.json"
OUTPUT_DIR = "../data/data_with_embeddings"

EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def generate_embeddings(input_file_path, output_dir, model_name):

    if not os.path.exists(input_file_path):
        logger.error(f"Input file not found: {input_file_path}")
        return
    
    logger.info(f"Loading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return
    
    logger.info(f"Reading data from {input_file_path}")

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            documents = json.load(f)

        logger.info(f"Loaded {len(documents)} Documents")

    except json.JSONDecodeError as e:
        logger.error(f"Error Decoding JSON from {input_file_path}")

    except Exception as e:
        logger.error(f"Error reading file {input_file_path}: {e}")
        return
    
    texts_to_embed = []
    processed_documents = []

    for doc in documents:
        sections = []

        # Add title if present
        if doc.get("title"):
            sections.append(doc["title"].strip())

        # Add headings if present and non-empty
        if doc.get("headings"):
            if isinstance(doc["headings"], list):
                headings = " ".join(h.strip() for h in doc["headings"] if h.strip())
                if headings:
                    sections.append(headings)
            elif isinstance(doc["headings"], str) and doc["headings"].strip():
                sections.append(doc["headings"].strip())

        # Add body if present
        if doc.get("body"):
            sections.append(doc["body"].strip())

        # Join all sections into one string
        combined_text = ' '.join(sections).strip()

        if combined_text:
            texts_to_embed.append(combined_text)
            processed_documents.append(doc)
        else:
            logger.warning(f"Skipping document {doc.get('id', doc.get('url', 'unknown'))} due to empty text content.")

    if not texts_to_embed:
       logger.warning("No valid text content found to generate embeddings for.")
       return 
    
    logger.info(f"Generating embeddings for {len(texts_to_embed)} documents...")

    try:
        embeddings = model.encode(texts_to_embed, batch_size= 32, show_progress_bar=True)
        logger.info("Embeddings generated successfully")
    except Exception as e:
        logger.error(f"Error generating embedding: {e}") 
        return
    
    
    for i, embeddings in enumerate(embeddings):
        processed_documents[i]['embedding_vector'] = embeddings.tolist()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_name = f"embeddings_{timestamp}.json"
    output_file_path = os.path.join(output_dir, output_file_name)

    logger.info(f"Saving processed data with embeddings to {output_file_path}...")
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(processed_documents, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved {len(processed_documents)} documents with embeddings.")
    except Exception as e:
        logger.error(f"Error saving output file {output_file_path}: {e}")


if __name__ == "__main__":
    generate_embeddings(CRAWLED_DATA, OUTPUT_DIR, EMBEDDING_MODEL)
