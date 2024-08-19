import streamlit as st
from dotenv import load_dotenv
import os
import json
from openai import OpenAI
from exa_py import Exa

load_dotenv()

class WebAgent:
    def __init__(self, num_search_results) -> None:
        self.search_client = Exa(api_key="e0985a36-3e58-407b-baf4-ee149437e47d")
        self.agent_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.num_search_results = num_search_results
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
        results = self.search_client.search_and_contents(
            query=query,
            type="auto",
            num_results=self.num_search_results,
            text=True
        ).results

        print("got results from search api")

        sources = []
        search_results = []
        for result in results:
            if result.url not in self.session_history:
                self.session_history.append(result.url)
                md_contents = self.summarize_content(result.text)
                metadata = {
                    "title": result.title,
                    "sourceURL": result.url,
                    "published_date": result.published_date
                }
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
                st.write({
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

tools = [
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Used to search for query in google and it'll returns list of urls and page contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A concise search query to sear for."
                    },
                },
                "required": ["query"]
            }
        }
    }
]

class Agent:
    def __init__(self, system_prompt, num_search_results) -> None:
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.search_agent = WebAgent(num_search_results)

        self.history = [
            {
                'role': 'system',
                'content': system_prompt
            }
        ]
    
    def send_message(self, msg):
        """
        Sends a message to the chat client and receives a response.

        Args:
            msg (str): The message to send.

        Returns:
            tuple: A tuple containing the response message and a list of sources.
                The response message is a string.
                The sources is a list of strings.
        """
        self.history.append(
            {
                'role': 'user',
                'content': msg
            }
        )

        response = self.client.chat.completions.create(
            messages=self.history,
            tools=tools,
            model='gpt-4o-mini',
            temperature=1.0,
            top_p=1.0
        )
        print(response)
        self.history.append(response.choices[0].message)

        if response.choices[0].message.tool_calls:
            tool_output = []
            sources = []
            for tool_call in response.choices[0].message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                # fcn...
                query = fn_args.get('query')
                st.write("Searching for: ", query)
                print("searching for: ", query)

                c, s = self.search_agent.get_content(query)
                print("got contents")
                for i in range(len(c)):
                    tool_output.append(c[i])
                    sources.append(s[i])
                print("Total sources collected: ", len(sources))

                self.history.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fn_name,
                        "content": str(tool_output),
                    }
                )
                
            return self.client.chat.completions.create(
                    messages=self.history,
                    model='gpt-4o-mini',
                    temperature=1.0,
                    top_p=1.0
                ).choices[0].message.content
        
        return response.choices[0].message.content

def main():
    st.title("search smart")

    if "agent" not in st.session_state:
        st.session_state.agent = None

    if "history" not in st.session_state:
        st.session_state.history = []
    
    for history in st.session_state.history:
        with st.chat_message(history["role"]):
            st.markdown(history["text"])
    
    with st.sidebar:
        st.title("Settings")
        num_search_results = st.slider("Number of search results", min_value=1, max_value=10, value=3, step=1)

        if st.button("Set"):
            st.session_state.agent = Agent(system_prompt=open("system_prompt.txt", 'r').read(), num_search_results=num_search_results)
            st.success("Ready to search!")

    if st.session_state.agent is not None:
        if prompt := st.chat_input("Enter your message..."):
            st.session_state.history.append({"role": "user", "text": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                response = st.session_state.agent.send_message(prompt)
                message_placeholder.markdown(response)
            st.session_state.history.append({"role": "assistant", "text": response})
        
if __name__ == '__main__':
    main()