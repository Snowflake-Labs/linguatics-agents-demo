#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging
import os
import queue
import threading
import uuid
import warnings

import streamlit as st

# Agent Gateway imports
from agent_gateway import Agent, TruAgent
from agent_gateway.tools import CortexAnalystTool, CortexSearchTool, PythonTool
from dotenv import load_dotenv

# Snowflake imports
from snowflake.snowpark import Session

# Trulens imports
from trulens.core.database.connector.default import DefaultDBConnector

from logging_util import setup_logging
from sarvam_ai_lang_tools import answer_translator, lang_detect, translate

load_dotenv()

warnings.filterwarnings("ignore", category=DeprecationWarning)

st.set_page_config(
    page_title="Linguatics Agents Demo",
    page_icon=":robot:",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.header("Linguatics Agents Demo")
st.subheader("Using Snowflake Cortex Analyst with Indic Languages")
st.markdown(
    "This demo showcases how to use Snowflake Cortex Analyst with Indic languages. "
    "You can ask questions in your preferred language, and the agent will respond accordingly."
)

OUTPUT_PROMPT = """
You are a helpful multi lingual analyst who can answer about customer support tickets. Guidelines for your tasks will be:
1. Translates the question from detected language to english
2. Send the translated question to the CortexAnalystTool to get the answer.
3. Translate the answer back to the original language of the question using the 'answer_translator' tool.
4. The answer should start with a marker 'Action: Finish' and end with a marker '<END_OF_RESPONSE>' with actual answer between the start and end marker.
"""

# Initialize session state variables with defaults if not already set
if "model_stage" not in st.session_state:
    __model_stage = os.getenv("SEMANTIC_MODEL_STAGE")
    if not __model_stage:
        raise ValueError("SEMANTIC_MODEL_FILE environment variable is not set.")
    st.session_state.model_stage = __model_stage

if "semantic_model_file" not in st.session_state:
    __semantic_model_file = os.getenv("SEMANTIC_MODEL_FILE")
    if not __semantic_model_file:
        raise ValueError("SEMANTIC_MODEL_FILE environment variable is not set.")
    st.session_state.semantic_model_file = __semantic_model_file

if "search_service_name" not in st.session_state:
    __search_service_name = os.getenv("SEARCH_SERVICE_NAME")
    if not __search_service_name:
        raise ValueError("SEARCH_SERVICE_NAME environment variable is not set.")
    st.session_state.search_service_name = __search_service_name

if "debug_mode" not in st.session_state:
    # Default debug mode is True for this demo
    st.session_state.debug_mode = True

if "sarvam_api_key" not in st.session_state:
    st.session_state.sarvam_api_key = os.getenv("SARVAM_API_KEY")

if "enable_truelens" not in st.session_state:
    st.session_state.enable_truelens = False

if "source_lang" not in st.session_state:
    st.session_state.source_lang = None

if "target_lang" not in st.session_state:
    # Default target language is English (India)
    # this will always be english for this demo as Cortex Analyst is trained on English data
    st.session_state.target_lang = "en-IN"


# Set up logging
if "logging_setup" not in st.session_state:
    st.session_state.logging_setup = setup_logging()
    st.logger = logging.getLogger("AgentGatewayLogger")  # type: ignore
    st.logger.propagate = True  # type: ignore


def build_agent():
    if st.session_state.enable_truelens:
        connector = DefaultDBConnector()
        agent = TruAgent(
            app_name="linguatics_agent_demo",
            app_version="v0.0.1",
            trulens_snowflake_connection=connector,
            snowflake_connection=st.session_state.snowpark,
            tools=st.session_state.snowflake_tools,
            max_retries=3,
        )
        # TODO
        # session = TruSession(connector=connector)
        # run_dashboard(session, port=8084, force=True)
    else:
        agent = Agent(
            snowflake_connection=st.session_state.snowpark,
            agent_llm="claude-3-5-sonnet",
            tools=st.session_state.snowflake_tools,
            fusion_prompt=OUTPUT_PROMPT,
        )
    return agent


## Snowflake Connection
if not os.getenv("PRIVATE_KEY_PASSPHRASE"):
    raise ValueError("PRIVATE_KEY_PASSPHRASE environment variable is not set.")


if not os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME"):
    raise ValueError(
        "SNOWFLAKE_DEFAULT_CONNECTION_NAME environment variable is not set."
    )

connection_parameters = {
    "connection_name": os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME"),
    "private_key_file_pwd": os.getenv("PRIVATE_KEY_PASSPHRASE"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "kamesh_llm_demo"),
    "user": os.getenv("SNOWFLAKE_USER", "kameshs"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "schema": "DATA",
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
}

if "snowpark" not in st.session_state or st.session_state.snowpark is None:
    st.session_state.snowpark = Session.builder.configs(
        connection_parameters
    ).getOrCreate()
    # IMPORTANT: Set the database, schema, and warehouse for the session
    st.session_state.snowpark.use_database(connection_parameters["database"])
    st.session_state.snowpark.use_schema(connection_parameters["schema"])
    st.session_state.snowpark.use_warehouse(connection_parameters["warehouse"])

    analyst_config = {
        "semantic_model": st.session_state.semantic_model_file,
        "stage": st.session_state.model_stage,
        "service_topic": "Customer support tickets model",
        "data_description": "a table with customer support tickets",
        "snowflake_connection": st.session_state.snowpark,
        "max_results": 5,
    }

    search_config = {
        "service_name": st.session_state.search_service_name,
        "service_topic": "Customer invoice related queries.",
        "data_description": "Customer invoices and related documents",
        "retrieval_columns": ["PARSED_TEXT", "URL"],
        "snowflake_connection": st.session_state.snowpark,
        "k": 10,
    }

    __language_identifier_config = {
        "tool_description": "Identify the language of the question",
        "output_description": "It should identify the language code and return it for other tools to use.",
        "python_func": lang_detect,
    }

    __translator_config = {
        "tool_description": "Use the identified language from the right tool (e.g., ta-IN for Tamil, hi-IN for Hindi, te-IN for Telugu) as the language code to translate the question to English and then pass the english question to Analyst tool.",
        "output_description": "Returns English translation of the question",
        "python_func": translate,
    }

    __answer_translator_config = {
        "tool_description": "Translate the answer from English back to the original language of the question.",
        "output_description": "Returns the answer translated from English to the original question's language.",
        "python_func": answer_translator,
    }

    # Tools Config
    st.session_state.language_identifier = PythonTool(**__language_identifier_config)
    st.session_state.translator = PythonTool(**__translator_config)
    st.session_state.answer_translator = PythonTool(**__answer_translator_config)
    st.session_state.analyst = CortexAnalystTool(**analyst_config)
    st.session_state.search_config = CortexSearchTool(**search_config)

    st.session_state.snowflake_tools = [
        st.session_state.language_identifier,
        st.session_state.translator,
        st.session_state.analyst,
        st.session_state.search_config,
        st.session_state.answer_translator,
    ]


if "agent" not in st.session_state:
    connector = DefaultDBConnector()
    st.session_state.agent = build_agent()


# Sidebar settings
# with st.sidebar:
#     st.header("⚙️ Settings")
#     st.subheader("Configure your agent")

#     st.session_state.enable_truelens = st.radio(
#         "Enable TruLens",
#         options=[True, False],
#         help="Enable TruLens for monitoring and debugging agent interactions.",
#         format_func=lambda x: "Enabled" if x else "Disabled",
#         index=1,
#     )
#     # st.session_state.debug_mode = st.radio(
#     #     "Debug Mode",
#     #     options=[True, False],
#     #     format_func=lambda x: "Enabled" if x else "Disabled",
#     #     help="Enable or disable debug mode.",
#     #     index=0,
#     #     key="debug",
#     # )

#     # if st.session_state.debug_mode and (
#     #     st.session_state.language_tools.detected_language
#     #     or st.session_state.language_tools.translation
#     # ):
#     #     t_lang = st.session_state.language_tools.target_language
#     #     s_lang = st.session_state.language_tools.detected_language
#     #     st.sidebar.markdown(f"Target Language:`{t_lang}`")
#     #     st.sidebar.markdown(
#     #         f"Identified Source Language:`{s_lang}`",
#     #     )
#     #     st.sidebar.text_area(
#     #         "Translation",
#     #         value=st.session_state.language_tools.translation or "No translation yet.",
#     #         height=100,
#     #         disabled=True,
#     #     )


def process_message(prompt_id: str):
    prompt = st.session_state["prompt_history"][prompt_id].get("prompt")

    message_queue = queue.Queue()
    agent = st.session_state.agent
    log_container = st.empty()
    log_handler = setup_logging()

    def run_analysis():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(agent.acall(prompt))
        loop.close()
        message_queue.put(response)

    thread = threading.Thread(target=run_analysis)
    thread.start()

    while True:
        try:
            response = message_queue.get(timeout=1)
            if isinstance(response, dict) and "output" in response:
                final_response = response
                st.session_state["prompt_history"][prompt_id]["response"] = (
                    final_response["output"]
                )
                st.session_state["prompt_history"][prompt_id]["sources"] = (
                    final_response["sources"]
                )
                logs = log_handler.process_logs()
                if logs:
                    log_container.code(logs)
                log_container.empty()
                yield final_response
                break
            else:
                logs = log_handler.process_logs()
                if logs:
                    log_container.code(logs)

        except queue.Empty:
            logs = log_handler.process_logs()
            if logs:
                log_container.code(logs)
    st.rerun()


def extract_tool_name(statement):
    start = statement.find("Running") + len("Running") + 1
    end = statement.find("tool")
    return statement[start:end].strip()


if "prompt_history" not in st.session_state:
    st.session_state["prompt_history"] = {}


def create_prompt(prompt_key: str):
    if prompt_key in st.session_state:
        prompt_record = dict(prompt=st.session_state[prompt_key], response="waiting")
        st.session_state["prompt_history"][str(uuid.uuid4())] = prompt_record


with st.container(border=False):
    for id in st.session_state.prompt_history:
        current_prompt = st.session_state.prompt_history.get(id)

        with st.chat_message("user"):
            st.write(current_prompt.get("prompt"))

        with st.chat_message("assistant"):
            response_container = st.empty()
            if current_prompt.get("response") == "waiting":
                # Start processing messages
                message_generator = process_message(prompt_id=id)

                with st.spinner("Awaiting Response..."):
                    for response in message_generator:
                        response_container.text(response)
            else:
                # Display the final response
                response_container.markdown(
                    current_prompt["response"],
                    unsafe_allow_html=True,
                )
                # Add sources section aligned to the right
                if current_prompt.get("sources") is not None:
                    citations_metadata = [
                        source["metadata"] for source in current_prompt.get("sources")
                    ]

                    sources = []
                    for item in citations_metadata:
                        if (
                            item is not None
                            and isinstance(item, list)
                            and len(item) > 0
                        ):
                            first_element = item[0]
                            if (
                                isinstance(first_element, dict)
                                and len(first_element) > 0
                            ):
                                sources.append(next(iter(first_element.values())))

                    # Filter out None values in sources list
                    sources = [source for source in sources if source is not None]

                    # Determine the sources to display
                    sources_display = ", ".join(sources) if sources else "N/A"

                    st.markdown(
                        f"""
                        <div style="text-align: right; font-size: 0.8em; font-style: italic; margin-top: 5px;">
                            <b>Sources</b>: {sources_display}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

st.chat_input(
    "Ask Anything",
    on_submit=create_prompt,
    key="chat_input",
    args=["chat_input"],
)
