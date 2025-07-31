import requests
import json
import logging
from urllib.parse import quote
import base64

class SolrCloudQueryEngine:
    def __init__(self, solr_urls=['http://localhost:8984/solr/search_collection', 
                                  'http://localhost:7574/solr/search_collection',
                                  ]):
        self.solr_urls = solr_urls
        self.current_url_index = 0
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_active_solr_url(self):
        """Get an active Solr URL with failover"""
        for i in range(len(self.solr_urls)):
            url = self.solr_urls[self.current_url_index]
            try:
                # Test if this Solr node is available
                response = requests.get(f"{url}/admin/ping", timeout=5)
                if response.status_code == 200:
                    return url
            except:
                pass
            
            # Try next URL
            self.current_url_index = (self.current_url_index + 1) % len(self.solr_urls)
        
        # If no URLs work, return the first one and let it fail
        return self.solr_urls[0]
    
    def simple_search(self, query, start=0, rows=10, sort=None):
        """Perform simple text search with SolrCloud failover"""
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
            'facet.field': ['domain', 'content_type'],
            'facet.mincount': 1
        }
        
        if sort:
            params['sort'] = sort
        
        try:
            response = requests.get(f"{solr_url}/select", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Search error with {solr_url}: {str(e)}")
            # Try with a different Solr node
            self.current_url_index = (self.current_url_index + 1) % len(self.solr_urls)
            if self.current_url_index != 0:  # Avoid infinite recursion
                return self.simple_search(query, start, rows, sort)
            return {'response': {'docs': [], 'numFound': 0}}
    
    def dsl_search(self, dsl_query):
        """Perform DSL-based search with SolrCloud failover"""
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
            'facet.field': ['domain', 'content_type'],
            'facet.mincount': 1
        }
        
        # Add sorting
        if 'sort' in dsl_query:
            sort_field = dsl_query['sort']['field']
            sort_direction = dsl_query['sort']['direction']
            params['sort'] = f"{sort_field} {sort_direction}"
        
        # Add boosting
        if 'boost' in dsl_query and dsl_query['boost']:
            boost_params = []
            for boost in dsl_query['boost']:
                boost_params.append(f"{boost['field']}^{boost['factor']}")
            params['qf'] = ' '.join(boost_params)
        
        try:
            response = requests.get(f"{solr_url}/select", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"DSL search error with {solr_url}: {str(e)}")
            # Try with a different Solr node
            self.current_url_index = (self.current_url_index + 1) % len(self.solr_urls)
            if self.current_url_index != 0:
                return self.dsl_search(dsl_query)
            return {'response': {'docs': [], 'numFound': 0}}
    

    def build_solr_query(self, dsl_query):
        """Build Solr query from DSL structure"""
        conditions = dsl_query.get('conditions', [])
        query_parts = []

        self.logger.info(f"Conditions: {conditions}")

        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')

            # Make sure value is string before formatting
            if isinstance(value, list):
                value = ' '.join(map(str, value))
            elif not isinstance(value, str):
                value = str(value)

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
                    query_parts.append(f"{field}:[{min_val} TO {max_val}]")

        return ' AND '.join(query_parts) if query_parts else '*:*'

    
    def autocomplete(self, query, field='title_suggest', limit=5):
        """Get autocomplete suggestions from SolrCloud"""
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
            self.logger.error(f"Autocomplete error with {solr_url}: {str(e)}")
            return []
    
    def get_cluster_status(self):
        """Get SolrCloud cluster status"""
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
        """Format Solr response for frontend"""
        docs = solr_response.get('response', {}).get('docs', [])
        num_found = solr_response.get('response', {}).get('numFound', 0)
        highlighting = solr_response.get('highlighting', {})
        facets = solr_response.get('facet_counts', {}).get('facet_fields', {})

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

            # Add highlighting if available
            if doc.get('id') in highlighting:
                hl = highlighting[doc['id']]
                if 'title' in hl:
                    formatted_doc['title'] = hl['title'][0]
                if 'body' in hl:
                    formatted_doc['body'] = ' '.join(hl['body'])

            formatted_docs.append(formatted_doc)

        # Format facets
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
            'cluster_status': self.get_cluster_status()
        }


if __name__ == "__main__":
    import sys
    try:
        encoded_args = sys.argv[1] if len(sys.argv) > 1 else {}
        decoded_json = base64.b64decode(encoded_args).decode('utf-8')
        args = json.loads(decoded_json)

        engine = SolrCloudQueryEngine()

        if "dsl_query" in args:
            # Run DSL search
            dsl_query = args["dsl_query"]
            result = engine.dsl_search(dsl_query)
            formatted = engine.format_response(result)
            print(json.dumps(formatted))
        
        elif args.get("autocomplete", False):
            # Run autocomplete
            query = args.get("query", "*:*")
            field = args.get("field", "title_suggest")
            limit = int(args.get("limit", 5))
            suggestions = engine.autocomplete(query, field, limit)
            print(json.dumps({"suggestions": suggestions}))

        else:
            # Default to simple search
            query = args.get("query", "*:*")
            limit = int(args.get("limit", 5))
            result = engine.simple_search(query, rows=limit)
            formatted = engine.format_response(result)
            print(json.dumps(formatted))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

