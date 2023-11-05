from autogen import oai
from autogen.agentchat.agent import Agent
from autogen.agentchat.assistant_agent import ConversableAgent
from typing import Callable, Dict, Optional, Union, List, Tuple, Any

system_message = """You are an expert in text analysis.
The user will give you TEXT to analyze.
The user will give you analysis INSTRUCTIONS copied twice, at both the beginning and the end.
You will follow these INSTRUCTIONS in analyzing the TEXT, then give the results of your expert analysis in the format requested."""


class TextAnalyzerAgent(ConversableAgent):
    """(Experimental) Text Analysis agent, a subclass of ConversableAgent designed to analyze text as instructed."""

    def __init__(
        self,
        name="analyzer",
        system_message: Optional[str] = system_message,
        human_input_mode: Optional[str] = "NEVER",
        llm_config: Optional[Union[Dict, bool]] = None,
        **kwargs,
    ):
        """
        Args:
            name (str): name of the agent.
            system_message (str): system message for the ChatCompletion inference.
            human_input_mode (str): This agent should NEVER prompt the human for input.
            llm_config (dict or False): llm inference configuration.
                Please refer to [OpenAIWrapper.create](/docs/reference/oai/client#create)
                for available options.
                To disable llm-based auto reply, set to False.
            teach_config (dict or None): Additional parameters used by TeachableAgent.
                To use default config, set to None. Otherwise, set to a dictionary with any of the following keys:
                - verbosity (Optional, int): # 0 (default) for basic info, 1 to add memory operations, 2 for analyzer messages, 3 for memo lists.
                - reset_db (Optional, bool): True to clear the DB before starting. Default False.
                - path_to_db_dir (Optional, str): path to the directory where the DB is stored. Default "./tmp/teachable_agent_db"
                - prepopulate (Optional, int): True (default) to prepopulate the DB with a set of input-output pairs.
                - recall_threshold (Optional, float): The maximum distance for retrieved memos, where 0.0 is exact match. Default 1.5. Larger values allow more (but less relevant) memos to be recalled.
                - max_num_retrievals (Optional, int): The maximum number of memos to retrieve from the DB. Default 10.
            **kwargs (dict): other kwargs in [ConversableAgent](../conversable_agent#__init__).
        """
        super().__init__(
            name=name,
            system_message=system_message,
            human_input_mode=human_input_mode,
            llm_config=llm_config,
            **kwargs,
        )
        self.register_reply(Agent, TextAnalyzerAgent._analyze_in_reply, 2)

    def _analyze_in_reply(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[Agent] = None,
        config: Optional[Any] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        """Analyzes the given text as instructed, and returns the analysis as a message.
        Assumes exactly two messages containing the text to analyze and the analysis instructions.
        See TeachableAgent.analyze for an example of how to use this method."""
        if self.llm_config is False:
            raise ValueError("TextAnalyzerAgent requires self.llm_config to be set in its base class.")
        if messages is None:
            messages = self._oai_messages[sender]  # In case of a direct call.
        assert len(messages) == 2

        # Delegate to the analysis method.
        return True, self.analyze_text(messages[0]["content"], messages[1]["content"])

    def analyze_text(self, text_to_analyze, analysis_instructions):
        """Analyzes the given text as instructed, and returns the analysis."""
        # Assemble the message.
        text_to_analyze = "# TEXT\n" + text_to_analyze + "\n"
        analysis_instructions = "# INSTRUCTIONS\n" + analysis_instructions + "\n"
        msg_text = "\n".join(
            [analysis_instructions, text_to_analyze, analysis_instructions]
        )  # Repeat the instructions.
        # Generate and return the analysis string.
        return self.generate_oai_reply([{"role": "user", "content": msg_text}], None, None)[1]
