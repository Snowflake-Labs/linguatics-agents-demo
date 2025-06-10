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
import io
import logging
import os
import queue
import re
import threading
import uuid
import warnings

import streamlit as st

# Agent Gateway imports
from agent_gateway import Agent, TruAgent
from agent_gateway.tools import CortexAnalystTool, PythonTool
from agent_gateway.tools.utils import parse_log_message
from dotenv import load_dotenv

# Sarvam imports
from sarvamai import SarvamAI

# Snowflake imports
from snowflake.snowpark import Session

# Trulens imports
from trulens.core.database.connector.default import DefaultDBConnector

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

# Initialize session state variables with defaults if not already set
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


class StreamlitLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_buffer = io.StringIO()
        self.ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    def emit(self, record):
        msg = self.format(record)
        clean_msg = self.ansi_escape.sub("", msg)
        self.log_buffer.write(clean_msg + "\n")

    def get_logs(self):
        return self.log_buffer.getvalue()

    def process_logs(self):
        raw_logs = self.get_logs()
        lines = raw_logs.strip().split("\n")
        log_output = [parse_log_message(line.strip()) for line in lines if line.strip()]
        cleaned_output = [line for line in log_output if line is not None]
        all_logs = "\n".join(cleaned_output)
        return all_logs

    def clear_logs(self):
        self.log_buffer = io.StringIO()


def setup_logging():
    root_logger = logging.getLogger()
    handler = StreamlitLogHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    return handler


# Set up logging
if "logging_setup" not in st.session_state:
    st.session_state.logging_setup = setup_logging()
    st.logger = logging.getLogger("AgentGatewayLogger")  # type: ignore
    st.logger.propagate = True  # type: ignore


class SarvamLanguageTools:
    """A class to handle language detection and translation using SarvamAI."""

    SPEAKER_GENDER = "Male"
    TRANSLATION_MODE = "classic-colloquial"
    SARVAM_MODEL = "mayura:v1"
    TARGET_LANGUAGE = "en-IN"  # Always translate to English (India)

    def __init__(self, logger, debug_mode: bool = True):
        self.sarvam_client = SarvamAI(
            api_subscription_key=os.getenv("SARVAM_API_KEY"),
        )
        self.logger = logger
        self.__detected_language = None
        self.target_language = "en-IN"
        self.__translation = None
        self.debug_mode = debug_mode

    @property
    def detected_language(self):
        return self.__detected_language

    @property
    def translation(self):
        return self.__translation

    def lang_detect(self, text: str) -> str | None:
        response = self.sarvam_client.text.identify_language(input=text)
        lang_code = response.language_code

        self.__detected_language = lang_code
        self.logger.info(f"Detected language: {lang_code}")  # type: ignore

        return lang_code  # Return the language code and the original text

    def translate(self, question: str) -> str:
        self.logger.info(
            f"Translating: {question} from {self.detected_language} to {self.target_language}"
        )

        response = self.sarvam_client.text.translate(
            input=question,
            source_language_code=self.detected_language,
            target_language_code=self.TARGET_LANGUAGE,
            speaker_gender=self.SPEAKER_GENDER,
            mode=self.TRANSLATION_MODE,
            model=self.SARVAM_MODEL,
            enable_preprocessing=False,
        )

        self.__translation = response.translated_text
        self.logger.info(f"Translation: {self.translation}")

        return self.__translation


def chunk_text(text, max_length=1000):
    """Splits text into chunks of at most max_length characters while preserving word boundaries."""
    chunks = []

    while len(text) > max_length:
        split_index = text.rfind(" ", 0, max_length)  # Find the last space within limit
        if split_index == -1:
            split_index = max_length  # No space found, force split at max_length

        chunks.append(text[:split_index].strip())  # Trim spaces before adding
        text = text[split_index:].lstrip()  # Remove leading spaces for the next chunk

    if text:
        chunks.append(text.strip())  # Add the last chunk

    return chunks


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
            tools=st.session_state.snowflake_tools,
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
    st.session_state.snowpark.use_database("kamesh_llm_demo")
    st.session_state.snowpark.use_schema(connection_parameters["schema"])
    st.session_state.snowpark.use_warehouse(connection_parameters["warehouse"])

    analyst_config = {
        "semantic_model": "support_tickets_semantic_model.yaml",
        "stage": "MY_MODELS",
        "service_topic": "Customer support tickets model",
        "data_description": "a table with customer support tickets",
        "snowflake_connection": st.session_state.snowpark,
        "max_results": 5,
    }

    st.session_state.language_tools = SarvamLanguageTools(
        logger=st.logger,  # type: ignore
        debug_mode=st.session_state.debug_mode,
    )

    __language_identifier_config = {
        "tool_description": "Identify the language of the question",
        "output_description": "The Indic language code of the question that will be used by the translator tool.",
        "python_func": st.session_state.language_tools.lang_detect,
    }

    __translator_config = {
        "tool_description": "If language detected is not English, translate the question to English before passing it to the Analyst tool.",
        "output_description": "english translation of the question",
        "python_func": st.session_state.language_tools.translate,
    }

    # Tools Config
    st.session_state.language_identifier = PythonTool(**__language_identifier_config)
    st.session_state.translator = PythonTool(**__translator_config)
    st.session_state.analyst = CortexAnalystTool(**analyst_config)

    st.session_state.snowflake_tools = [
        st.session_state.language_identifier,
        st.session_state.translator,
        st.session_state.analyst,
    ]


if "agent" not in st.session_state:
    connector = DefaultDBConnector()
    st.session_state.agent = build_agent()


# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")
    st.subheader("Configure your agent")

    st.session_state.enable_truelens = st.radio(
        "Enable TruLens",
        options=[True, False],
        help="Enable TruLens for monitoring and debugging agent interactions.",
        format_func=lambda x: "Enabled" if x else "Disabled",
        index=1,
    )
    st.session_state.debug_mode = st.radio(
        "Debug Mode",
        options=[True, False],
        format_func=lambda x: "Enabled" if x else "Disabled",
        help="Enable or disable debug mode.",
        index=0,
        key="debug",
    )

    if st.session_state.debug_mode and (
        st.session_state.language_tools.detected_language
        or st.session_state.language_tools.translation
    ):
        t_lang = st.session_state.language_tools.target_language
        s_lang = st.session_state.language_tools.detected_language
        st.sidebar.markdown(f"Target Language:`{t_lang}`")
        st.sidebar.markdown(
            f"Identified Source Language:`{s_lang}`",
        )
        st.sidebar.text_area(
            "Translation",
            value=st.session_state.language_tools.translation or "No translation yet.",
            height=100,
            disabled=True,
        )


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
