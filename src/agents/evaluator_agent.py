from src.agents.base import Agent, DEFAULT_MODEL
from src.agents.schemas import EvaluationResult
from langchain.output_parsers import PydanticOutputParser
from typing import List, Optional, Dict
from src.metadata import add_evaluation_metadata


class EvaluatorAgent(Agent):
    def __init__(self, client, model = DEFAULT_MODEL):
        sys_prompt = """
        You are an expert evaluator in structured supply chain research.
        
        Your goals:
        1. You want to judge the quality of the given JSON document against a gold reference JSON document.
        2. Additionally, you want to evaluate the given subdimensions for their accuracy in the context of agentic AI in supply chains.
        3. As an output please:
        - Provide a score between 0 and 1 for each field present in the evaluated document.
        - If deemed necessary, provide any subdimension scores according to the EvaluationResult schema, otherwise omit them.
        - Provide any notes to explain your reasoning for the score.
        - Output as valid JSON matching the EvaluationResult schema.
        """
        super().__init__(
            role="Evaluator",
            version="1.0",
            sys_prompt=sys_prompt,
            tools=[],
            client=client,
            model=model,
        )

    def go_to_work(self, pred_json: dict, gold_json: dict):
        """
        Perform evaluation and return a structured EvaluationResult.

        Args:
            pred_json (dict): The JSON document to be evaluated.
            gold_json (dict): The reference JSON document.
        """

        # Build user input for agent
        user_input = f"""
            Document to be evaluated:
            {pred_json.get('content', {})}
            
            Gold reference:
            {gold_json}
        """

        # Prompt the agent
        parser = PydanticOutputParser(pydantic_object=EvaluationResult)
        model_output = self.prompt(user_input=user_input, parser=parser)
        model_output.compute_overall_score()

        pred_id = pred_json.get("metadata", {}).get("source", {}).get("doc_id", "unknown")
        eval_id = gold_json.get("metadata", {}).get("source", {}).get("doc_id", "unknown")

        combined_output = {}
        combined_output["metadata"] = pred_json.get("metadata", {})
        combined_output["content"] = model_output.model_dump()
        final_output = add_evaluation_metadata(combined_output, pred_id, eval_id, self.model)

        return final_output