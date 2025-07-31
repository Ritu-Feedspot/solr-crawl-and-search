import json
import requests
import logging
from datetime import datetime
import os
import time

class SolrCloudIndexer:
    def __init__(self, solr_urls=['http://localhost:8984/solr/search_collection',
                                  'http://localhost:7574/solr/search_collection',
                                  'http://localhost:8985/solr/search_collection']):
        self.solr_urls = solr_urls
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('../logs/indexer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_active_solr_url(self):
        """Get an active Solr URL for indexing"""
        for url in self.solr_urls:
            try:
                response = requests.get(f"{url}/admin/ping", timeout=5)
                if response.status_code == 200:
                    return url
            except:
                continue
        
        # If no URLs work, return the first one and let it fail
        self.logger.warning("No active Solr nodes found, using first URL")
        return self.solr_urls[0]
    
    def prepare_document(self, doc):
        """Prepare document for Solr indexing"""
        from urllib.parse import urlparse
        
        parsed_url = urlparse(doc['url'])
        domain = parsed_url.netloc
        
        solr_doc = {
            'id': doc['id'],
            'url': doc['url'],
            'title': doc['title'],
            'body': doc['body'],
            'meta_description': doc.get('meta_description', ''),
            'headings': doc.get('headings', []),
            'crawl_date': doc['crawl_date'],
            'last_modified': datetime.now().isoformat() + 'Z',
            'content_type': 'text/html',
            'domain': domain
        }
        
        return solr_doc
    
    def index_documents(self, documents, batch_size=100):
        """Index documents to SolrCloud with batching"""
        if not documents:
            self.logger.warning("No documents to index")
            return False
        
        solr_url = self.get_active_solr_url()
        total_docs = len(documents)
        indexed_count = 0
        
        # Process in batches
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            solr_docs = [self.prepare_document(doc) for doc in batch]
            
            try:
                # Add documents to Solr
                response = requests.post(
                    f"{solr_url}/update/json/docs",
                    json=solr_docs,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                response.raise_for_status()
                
                indexed_count += len(solr_docs)
                self.logger.info(f"Indexed batch {i//batch_size + 1}: {len(solr_docs)} documents ({indexed_count}/{total_docs})")
                
                # Small delay between batches
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error indexing batch {i//batch_size + 1}: {str(e)}")
                # Try with a different Solr node
                solr_url = self.get_active_solr_url()
                continue
        
        # Commit changes
        try:
            commit_response = requests.post(
                f"{solr_url}/update",
                json={'commit': {}},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            commit_response.raise_for_status()
            
            self.logger.info(f"Successfully indexed and committed {indexed_count} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error committing documents: {str(e)}")
            return False
    
    def delete_all_documents(self):
        """Delete all documents from SolrCloud collection"""
        solr_url = self.get_active_solr_url()
        
        try:
            response = requests.post(
                f"{solr_url}/update",
                json={'delete': {'query': '*:*'}},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            # Commit changes
            commit_response = requests.post(
                f"{solr_url}/update",
                json={'commit': {}},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            commit_response.raise_for_status()
            
            self.logger.info("Successfully deleted all documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    def get_collection_status(self):
        """Get collection status across all nodes"""
        status = {}
        for i, url in enumerate(self.solr_urls):
            try:
                response = requests.get(f"{url}/admin/ping", timeout=5)
                if response.status_code == 200:
                    # Get document count
                    count_response = requests.get(f"{url}/select?q=*:*&rows=0&wt=json", timeout=5)
                    doc_count = count_response.json().get('response', {}).get('numFound', 0)
                    
                    status[f"node_{i+1}"] = {
                        "url": url,
                        "status": "active",
                        "document_count": doc_count
                    }
                else:
                    status[f"node_{i+1}"] = {
                        "url": url,
                        "status": "inactive"
                    }
            except Exception as e:
                status[f"node_{i+1}"] = {
                    "url": url,
                    "status": "error",
                    "error": str(e)
                }
        return status
    
    def index_from_file(self, json_file):
        """Index documents from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            self.logger.info(f"Loading {len(documents)} documents from {json_file}")
            return self.index_documents(documents)
            
        except Exception as e:
            self.logger.error(f"Error reading file {json_file}: {str(e)}")
            return False

if __name__ == "__main__":
    indexer = SolrCloudIndexer()
    
    # Show collection status
    print("SolrCloud Collection Status:")
    print(json.dumps(indexer.get_collection_status(), indent=2))
    
    # Find the latest crawled data file
    data_dir = '../data'
    if os.path.exists(data_dir):
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        if json_files:
            latest_file = max(json_files)
            file_path = os.path.join(data_dir, latest_file)
            print(f"\nIndexing from: {file_path}")
            indexer.index_from_file(file_path)
        else:
            print("No JSON files found in data directory")
    else:
        print("Data directory not found")
