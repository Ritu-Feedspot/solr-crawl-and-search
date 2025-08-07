import json
import requests
import logging
from datetime import datetime
import os
import time
import sys
import base64
import traceback
from sentence_transformers import SentenceTransformer
import pysolr
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

class SolrCloudQueryEngine:
    def __init__(self, solr_urls=['http://localhost:8984/solr/search_collection', 
                                  'http://localhost:7574/solr/search_collection',
                                  ]):
        self.solr_urls = solr_urls
        self.current_url_index = 0
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        logging.disable(logging.CRITICAL)
        self.logger = logging.getLogger(__name__) # Still keep logger for potential future use

    def get_active_solr_url(self):
        initial_index = self.current_url_index
        for _ in range(len(self.solr_urls)):
            url = self.solr_urls[self.current_url_index]
            try:
                response = requests.get(f"{url}/admin/ping", timeout=5)
                if response.status_code == 200:
                    return url
            except requests.exceptions.RequestException:
                self.logger.error(f"Solr node {url} is unreachable. Trying next...")
            
            self.current_url_index = (self.current_url_index + 1) % len(self.solr_urls)
            if self.current_url_index == initial_index:
                break
        
        self.logger.warning("No active Solr nodes found, returning first URL. Search may fail.")
        return self.solr_urls[0]
    
    def _build_filter_queries(self, facets):
        fq_list = []
        if facets:
            for field, values in facets.items():
                if values and isinstance(values, list):
                    # Escape values for Solr query
                    escaped_values = [f'"{val.replace("\"", "\\\"")}"' for val in values]
                    # Tag the filter query for exclusion in facet counts
                    fq_list.append(f'{{!tag={field}_filter}}{field}:({" OR ".join(escaped_values)})')
        return fq_list

    def generate_query_embedding(self, query_text):
        if not query_text:
            return []
        return self.embedding_model.encode(query_text).tolist()

    def simple_search(self, query, start=0, rows=10, sort=None, facets=None):
        solr_url = self.get_active_solr_url()
        
        params = {
            'q': query,
            'start': start,
            'rows': rows,
            'wt': 'json',
            'hl': 'true',
            'hl.fl': 'title,body',
            'hl.simple.pre': '<mark>',
            'hl.simple.post': '</mark>',
            'facet': 'true',
            'facet.mincount': 1,
            'fl': '*,score', 
            'debugQuery': 'true' 
        }
        
        params['facet.field'] = [
            '{!ex=domain_filter}domain'
        ]
        
        if sort:
            params['sort'] = sort
        
        filter_queries = self._build_filter_queries(facets)
        if filter_queries:
            params['fq'] = filter_queries 

        try:
            response = requests.get(f"{solr_url}/select", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error during simple search {query}: {str(e)}")
            return {'response': {'docs': [], 'numFound': 0}}
    
    def semantic_search(self, query_text, start=0, rows=10, facets=None):
        solr_url = self.get_active_solr_url()
        
        query_vector = self.generate_query_embedding(query_text)
        if not query_vector:
            return {'response': {'docs': [], 'numFound': 0}}

        topK = max(rows, 100) 
        
        vector_string = json.dumps(query_vector)
        
        solr_client = pysolr.Solr(solr_url, always_commit=True, timeout=10)

        params = {
            'start': start,
            'rows': rows,
            'fl': '*,score', 
            'hl': 'true',
            'hl.fl': 'title,body',
            'hl.simple.pre': '<mark>',
            'hl.simple.post': '</mark>',
            'facet': 'true',
            'facet.mincount': 1,
            'debugQuery': 'true', 
            'facet.field': ['{!ex=domain_filter}domain'] 
        }
        
        filter_queries = self._build_filter_queries(facets)
        if filter_queries:
            params['fq'] = filter_queries

        try:
            results = solr_client.search(
                q=f"{{!knn f=embedding_vector topK={topK}}}{vector_string}",
                search_handler='/select', 
                method='POST', 
                **params 
            )
            return results.raw_response 
        except Exception as e:
            self.logger.error(f"Error during semantic search {query_text}: {str(e)}")
            self.current_url_index = (self.current_url_index + 1) % len(self.solr_urls)
            if self.current_url_index != (self.solr_urls.index(solr_url) + 1) % len(self.solr_urls):
                return self.semantic_search(query_text, start, rows, facets)
            return {'response': {'docs':[], 'numFound': 0}} 

    def dsl_search(self, dsl_query):
        solr_url = self.get_active_solr_url()
        solr_query = self.build_solr_query(dsl_query)
        
        params = {
            'q': solr_query,
            'start': dsl_query.get('start', 0),
            'rows': dsl_query.get('rows', 10),
            'wt': 'json',
            'hl': 'true',
            'hl.fl': 'title,body',
            'hl.simple.pre': '<mark>',
            'hl.simple.post': '</mark>',
            'facet': 'true',
            'facet.mincount': 1,
            'fl': '*,score', 
            'debugQuery': 'true' 
        }
        params['facet.field'] = [
            '{!ex=domain_filter}domain',
        ]
        
        if 'sort' in dsl_query:
            sort_field = dsl_query['sort']['field']
            sort_direction = dsl_query['sort']['direction']
            params['sort'] = f"{sort_field} {sort_direction}"
        
        if 'boost' in dsl_query and dsl_query['boost']:
            boost_params = []
            for boost in dsl_query['boost']:
                boost_params.append(f"{boost['field']}^{boost['factor']}")
            params['qf'] = ' '.join(boost_params)

        filter_queries = self._build_filter_queries(dsl_query.get('facets'))
        if filter_queries:
            params['fq'] = filter_queries
        
        try:
            response = requests.get(f"{solr_url}/select", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error during DSL search: {str(e)}")
            return {'response': {'docs': [], 'numFound': 0}}
  
    def build_solr_query(self, dsl_query):
        conditions = dsl_query.get('conditions', [])
        query_parts = []

        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')

            if not value or (isinstance(value, str) and not value.strip()):
                continue

            if isinstance(value, list):
                value = ' '.join(map(str, value))
            elif not isinstance(value, str):
                value = str(value)

            if operator != 'contains':
                value = value.replace('"', '\\"')

            if operator == 'contains':
                query_parts.append(f"{field}:*{value}*")
            elif operator == 'exact':
                query_parts.append(f"{field}:\"{value}\"")
            elif operator == 'starts_with':
                query_parts.append(f"{field}:{value}*")
            elif operator == 'ends_with':
                query_parts.append(f"{field}:*{value}")
            elif operator == 'range':
                if isinstance(value, str) and ',' in value:
                    min_val, max_val = value.split(',', 1)
                    query_parts.append(f"{field}:[{min_val.strip()} TO {max_val.strip()}]")

        final_query = ' AND '.join(query_parts) if query_parts else '*:*'
        return final_query

    def autocomplete(self, query, field='title_suggest', limit=5):
        solr_url = self.get_active_solr_url()
        
        params = {
            'suggest': 'true',
            'suggest.dictionary': 'mySuggester',
            'suggest.q': query,
            'suggest.count': limit,
            'wt': 'json'
        }
        
        try:
            response = requests.get(f"{solr_url}/suggest", params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            suggestions = []
            suggest_data = data.get('suggest', {}).get('mySuggester', {})
            if query in suggest_data:
                for suggestion in suggest_data[query]['suggestions']:
                    suggestions.append(suggestion['term'])
            
            return suggestions
        except Exception as e:
            self.logger.error(f"Error during autocomplete for query '{query}': {str(e)}")
            return []
    
    def get_cluster_status(self):
        status = {}
        for i, url in enumerate(self.solr_urls):
            try:
                response = requests.get(f"{url}/admin/ping", timeout=5)
                status[f"node_{i+1}"] = {
                    "url": url,
                    "status": "active" if response.status_code == 200 else "inactive",
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                status[f"node_{i+1}"] = {
                    "url": url,
                    "status": "inactive",
                    "error": str(e)
                }
        return status
  
    def format_response(self, solr_response):
        docs = solr_response.get('response', {}).get('docs', [])
        num_found = solr_response.get('response', {}).get('numFound', 0)
        highlighting = solr_response.get('highlighting', {})
        facets = solr_response.get('facet_counts', {}).get('facet_fields', {})
        debug_info = solr_response.get('debug', {}) # Correct: Extract debug info

        formatted_docs = []
        for doc in docs:
            # Normalize body to string (handle multiValued lists)
            body = doc.get('body', '')
            if isinstance(body, list):
                body_text = ' '.join(body)
            else:
                body_text = str(body)

            formatted_doc = {
                'id': doc.get('id'),
                'title': doc.get('title', ''),
                'url': doc.get('url', ''),
                'body': body_text[:300] + '...' if body_text else '',
                'meta_description': doc.get('meta_description', ''),
                'score': doc.get('score', 0), 
                'last_modified': doc.get('last_modified', ''),
                'domain': doc.get('domain', '')
            }

            if doc.get('id') in highlighting:
                hl = highlighting[doc['id']]
                if 'title' in hl:
                    formatted_doc['title'] = hl['title'][0]
                if 'body' in hl:
                    formatted_doc['body'] = ' '.join(hl['body'])

            formatted_docs.append(formatted_doc)

        formatted_facets = {}
        for field, values in facets.items():
            formatted_facets[field] = {}
            for i in range(0, len(values), 2):
                if i + 1 < len(values):
                    formatted_facets[field][values[i]] = values[i + 1]

        return {
            'docs': formatted_docs,
            'numFound': num_found,
            'facets': formatted_facets,
            'cluster_status': self.get_cluster_status(),
            'debug': debug_info 
        }

if __name__ == "__main__":
    try:
        logging.disable(logging.CRITICAL)
        
        encoded_args = sys.argv[1] if len(sys.argv) > 1 else '{}'
        decoded_json = base64.b64decode(encoded_args).decode('utf-8')
        args = json.loads(decoded_json)

        engine = SolrCloudQueryEngine()

        if "dsl_query" in args:
            dsl_query = args["dsl_query"]
            result = engine.dsl_search(dsl_query)
            formatted = engine.format_response(result)
            print(json.dumps(formatted))
        
        elif args.get("autocomplete", False):
            query = args.get("query", "*:*")
            field = args.get("field", "title_suggest")
            limit = int(args.get("limit", 5))
            suggestions = engine.autocomplete(query, field, limit)
            print(json.dumps({"suggestions": suggestions}))

        elif args.get("semantic_search", False): 
            query = args.get("query", "*:*")
            start = int(args.get("start", 0))
            rows = int(args.get("rows", 10))
            facets = args.get("facets", None)
            result = engine.semantic_search(query, start=start, rows=rows, facets=facets)
            formatted = engine.format_response(result)
            print(json.dumps(formatted))

        else:
            query = args.get("query", "*:*")
            start = int(args.get("start", 0))
            rows = int(args.get("rows", 10))
            facets = args.get("facets", None)
            result = engine.simple_search(query, start=start, rows=rows, facets=facets)
            formatted = engine.format_response(result)
            print(json.dumps(formatted))

    except Exception as e:
        error_details = {
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc(),
            "args_received": sys.argv if 'sys' in locals() else []
        }
        print(json.dumps(error_details))
