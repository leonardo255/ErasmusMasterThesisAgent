from langchain.messages import HumanMessage
import copy
from langchain.agents import create_agent
from langchain_core.output_parsers import PydanticOutputParser
from src.agents.schemas import Dimensions
from src.metadata import add_agent_metadata



class DimensionExtractor():
    def __init__(self, model, sys_prompt):
        
        self.sys_prompt = sys_prompt

        self.role           = "Dimension Extractor Agent"
        self.version        = "1.0"
        self.model          = model

        self.agent = create_agent(
            model           = self.model,
            tools           = [],
            system_prompt   = self.sys_prompt,
            #checkpointer   = self.checkpointer,
            middleware      = [],
        )

    def invoke(self, user_msg: HumanMessage):
        messages = [user_msg]
        response = self.agent.invoke(
            {"messages": messages},
            config={
                "configurable": {"thread_id": "1"},
                "max_concurrency": 1,     # 🔒 enforce sequential tool execution
            }
        )
        
        return response
    
    
    def go_to_work(self, user_instructions: str, input_data: dict):

        _input_data = copy.deepcopy(input_data)

        parser = PydanticOutputParser(pydantic_object=Dimensions)
        prompt = f"{user_instructions}\n\n{_input_data.get('chunks', [])}"

        if parser:
            prompt += "\n\n" + parser.get_format_instructions()


        response = self.invoke(HumanMessage(content=prompt))
        messages = response.get("messages", [])
        
        # Extract the text content from the last AI message
        model_output_text = ""
        if messages:
            last_message = messages[-1]
            model_output_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        if parser:
            try:
                parsed_result = parser.parse(model_output_text)
                # Convert Pydantic model to dict for JSON serialization
                return parsed_result.model_dump() if hasattr(parsed_result, 'model_dump') else parsed_result.dict()
            except Exception as e:
                return {"error": f"Parser failed: {e}", "raw_output": model_output_text}

        combined_output = {}
        combined_output["metadata"] = _input_data.get("metadata", {})
        combined_output["content"] = model_output_text
        final_output = add_agent_metadata(document=combined_output, 
                                          agent_name=self.role, 
                                          agent_version=self.version,
                                          agent_model=self.model
                                          )

        return final_output