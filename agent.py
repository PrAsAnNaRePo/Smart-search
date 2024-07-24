import os
import json
from openai import OpenAI
from web_scrapper import WebAgent

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
    def __init__(self, system_prompt) -> None:
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.search_agent = WebAgent()

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

        self.history.append(response.choices[0].message)

        if response.choices[0].message.tool_calls:
            tool_output = []
            sources = []
            for tool_call in response.choices[0].message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                # fcn...
                query = fn_args.get('query')
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
                ).choices[0].message.content, sources
        
        return response.choices[0].message.content, None