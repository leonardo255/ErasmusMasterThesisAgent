from langchain.messages import HumanMessage
import copy
from langchain.agents import create_agent
from langchain_core.output_parsers import PydanticOutputParser
from src.agents.schemas import Dimensions
from src.metadata import add_agent_metadata


DEFAULT_SYSTEM_PROMPT = """
You are an expert academic analyst specializing in Digital Supply Networks and Artificial Intelligence.

Your goal is to analyze research papers and extract structured data across supply chain sectors.

Your input will be in JSON format containing the parsed content of research papers.

Analyze the content based on the following dimensions. If information is not explicitly present, leave the field empty.

1. DCM Capability (The Classification):
Classify the paper's main focus into ONE of the following 6 DCM capabilities based on the definitions below:

- Connected Customer:
    Focus: Engaging customers throughout the lifecycle (acquisition to service).
    Key Concepts: Service lifecycles, real-time signal sensing, location awareness, predictive issue resolution, customer satisfaction & loyalty.
    Typical Role: Field Service Manager (managing technicians, repairs, contracts) or Customer Experience Managers.

- Product Development:
    Focus: Conceptualizing, designing, and launching products responsive to customer needs.
    Key Concepts: R&D, rapid prototyping, PLM (Product Lifecycle Management), agile innovation, cross-functional design collaboration, time-to-market acceleration.
    Typical Role: Design Engineer (prototyping) or Manufacturing Engineer (new product introduction).

- Synchronized Planning:
    Focus:* Aligning strategic, financial, and operational plans across the entire network.
    Key Concepts:* Demand forecasting, S&OP (Sales and Operations Planning), inventory positioning, financial planning, network capacity planning, "digital twin" simulations.
    Typical Role:* Network Planner (balancing resources and demand).

- Intelligent Supply:
    Focus:* Sourcing goods and services at best value while mitigating risk.
    Key Concepts: Procurement, supplier relationship management (SRM), automated requisitions, contract management, spend analysis, supplier risk monitoring.
    Typical Role: Procurement Manager (sourcing components, minimizing costs).

- Smart Operations:
    Focus: Synchronizing production and manufacturing execution.
    Key Concepts: Manufacturing execution systems (MES), shop-floor automation, Industry 4.0, predictive maintenance, quality control, safety management, asset performance.
    Typical Role: Operations Command Center Director or Plant Manager.

- Dynamic Fulfillment:
    Focus:* Logistics, warehousing, and transportation to deliver the right product at the right time.
    Key Concepts: Warehouse management (WMS), transportation management (TMS), last-mile delivery, order fulfillment, reverse logistics (returns), distributed order management.
    Typical Role: Warehouse Director or Logistics Manager.

2. SCOR_Process (Traditional View):
Classify the primary process addressed based on the SCOR model:
- Plan: Demand/Supply planning, balancing resources, strategy.
- Source: Sourcing, procurement, supplier selection, receiving goods.
- Make: Production, manufacturing, assembly, maintenance.
- Deliver: Order management, warehousing, transportation, installation.
- Return: Reverse logistics, returns, repair, overhaul.
- Enable: Managing business rules, performance, data, risk, and compliance.
    
3. SCRM_Area (Risk Management):
If the paper addresses Supply Chain Risk Management, classify the type of risk:
- Supply Risk (Disruptions, supplier bankruptcy, raw material shortage).
- Demand Risk (Volatility, forecasting errors, panic buying).
- Operational Risk (Machine breakdown, internal process failure, labor strikes).
- Cyber/Information Risk (Data breaches, IT failure, digital security).
- Sustainability/Regulatory Risk (Compliance, environmental impact).
- None (If the paper is purely about optimization/efficiency without a risk focus).     
    
4. Problem_Description:
- A concise (1 sentence) description of the specific supply chain issue or pain point addressed in the paper

5. AI Technology & Agentic Nature:
- Specific Algorithm: Identify the specific AI model or technique used (e.g., Deep Reinforcement Learning, Transformer, Genetic Algorithm, SVM).
- Is Agentic: (True/False). Does the paper explicitly describe an "Agent", "Autonomous Agent", or "Multi-Agent System" (MAS) that perceives and acts without human intervention?
- Agent Role: If 'Is Agentic' is True, describe briefly what the agent does (e.g., "The agent autonomously negotiates directly with suppliers" or "The agent reroutes trucks in real-time").

6. Industry / Sector:
- Identify the specific industry where the case study is applied (e.g., Automotive, Pharmaceutical, Fashion, Aerospace).
- If the paper is a general review or purely theoretical without a specific industry application, output "General".

Your output should be a valid JSON object matching the Dimensions schema.
"""


class DimensionExtractor():
    def __init__(self, model, sys_prompt=None):
        if sys_prompt is None:
            sys_prompt = DEFAULT_SYSTEM_PROMPT
        
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