from abc import abstractmethod
from langchain.agents import create_agent
from langchain.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver


class Agent:
    def __init__(self, role, version, sys_prompt, tools, model):
        self.role           = role
        self.version        = version
        self.model          = model
        self.tools          = tools
        self.sys_prompt     = sys_prompt
        #self.checkpointer   = InMemorySaver()
        self.messages = [
            {"role": "system", "content": sys_prompt}
        ]
        self.init_agent()

    def init_agent(self):
        # Init agent
        self.agent = create_agent(
            model           = self.model,
            tools           = self.tools,
            system_prompt   = self.sys_prompt,
            #checkpointer    = self.checkpointer,
            middleware      = [],
        )

    def prompt(self, user_input: str, parser=None):

        if parser:
            user_input += "\n\n" + parser.get_format_instructions()

        #self.messages.append({"role": "user", "content": user_input})

        messages = [
            *self.messages,
            {"role": "user", "content": user_input}
        ]

        response = self.client.chat.completions.create(
            model       = self.model,
            messages    = messages,
            tools       = self.tools,
            max_turns   = 5
        )
        output = response.choices[0].message.content.strip()
        #self.messages.append({"role": "assistant", "content": output})
        
        if parser:
            try:
                return parser.parse(output)
            except Exception as e:
                return {"error": f"Parser failed: {e}", "raw_output": output}
            
        return output

    @abstractmethod
    def go_to_work(self, *args, **kwargs):
        """
        Abstract method for agent-specific logic:
        - Input preparation
        - Calling self.prompt()
        - Post-processing / merging metadata
        - Returning structured output
        """
        pass