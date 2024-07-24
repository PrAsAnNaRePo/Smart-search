from firecrawl import FirecrawlApp
from openai import OpenAI
import os

class WebAgent:
    def __init__(self) -> None:
        self.search_client = FirecrawlApp(api_key=os.environ.get('FIRECRAWL_API_KEY'))
        self.agent_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

        self.params = {
            "searchOptions": {
                "limit": 3
            }
        }

        self.session_history = []

    def get_content(self, query):
        """
        Retrieves content from the search API based on the given query.

        Args:
            query (str): The search query to retrieve content for.

        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, str]]]: A tuple containing two lists. The first list contains
            dictionaries representing the search results, with each dictionary containing the metadata and content of a
            search result. The second list contains dictionaries representing the sources of the search results, with each
            dictionary containing the title and URL of a source.

        """
        results = self.search_client.search(query, params=self.params)
        print("got results from search api")
        sources = []
        search_results = []
        for result in results:
            if result['metadata']['sourceURL'] not in self.session_history:
                self.session_history.append(result['metadata']['sourceURL'])
                md_contents = self.summarize_content(result['markdown'])
                metadata = result['metadata']
                search_results.append(
                    {
                        'metadata': metadata,
                        'content': md_contents
                    }
                )
                sources.append({
                    "title": metadata['title'],
                    'url': metadata['sourceURL']
                })
            else:
                continue
        return search_results, sources

    def summarize_content(self, content):
        """
        Summarizes the given web content based on a query.

        Args:
            content (str): The raw web content to be summarized.

        Returns:
            str: The summarized and relevant content based on the query.
        """
        return self.agent_client.chat.completions.create(
            messages=[
                {
                    'role': 'system',
                    'content': 'you are a web content summarizer. your main job is to summarize the given raw web contents into meaningful and related contents based on the given query. make sure you removed the unwanted content and have all the related contents.'
                },
                {
                    'role': 'user',
                    'content': f"Here is the raw-content: {content}\n\nPlease summarize and extract the relevant contents into concise form."
                }
            ],
            model='gpt-4o-mini',
            temperature=1.0,
            top_p=1.0
        ).choices[0].message.content

# agent=WebAgent()
# print(agent.get_content("fish oil capsules"))


# pip install -r requirements.txt