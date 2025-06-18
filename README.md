# Linguatics Agents Demo

A [Streamlit](https://streamlit.io) application demonstrating the use of [Snowflake Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst), [Snowflake Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview) and [Snowflake Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents) with Indic languages, featuring automatic language detection and translation capabilities powered by [SarvamAI](https://sarvam.ai).

This demo leverages Snowflake's [Orchestration Framework](https://github.com/snowflake-labs/orchestration-framework) to build sophisticated multilingual AI agents capable of analyzing customer support tickets across various Indic languages. The orchestration framework provides a powerful foundation for creating Agentic AI workflows that can handle complex multi-step processes, tool integrations, and state management.

Key orchestration capabilities utilized in this demo:

- **Multi-tool Coordination**: Seamlessly orchestrates language detection, translation, and data analysis tools
- **Workflow Management**: Handles complex agent workflows with proper error handling and state transitions
- **Tool Integration**: Provides standardized interfaces for integrating external APIs (SarvamAI) with Snowflake services
- **Async Processing**: Supports non-blocking operations for better user experience
- **Agent Gateway**: Utilizes Snowflake's native agent orchestration capabilities for scalable deployment

This architecture ensures a seamless user experience for non-English speakers while maintaining the flexibility to extend functionality and integrate additional tools as needed.

> [!IMPORTANT]
> **Disclaimer:**
> This project is at a very experimental stage and is subject to significant changes. It is not yet ready for production use.

## Overview

This demo showcases how to build multilingual AI agents that can:

- Detect the language of user questions in various Indic languages
- Translate questions to English for processing by Snowflake Cortex Analyst
- Provide responses to customer support ticket analysis queries in the same language as the input
- Support debugging and monitoring with optional TruLens integration

## Features

- [x] **🌐 Multilingual Support**: Supports multiple Indic languages including Hindi, Tamil, Telugu, Kannada, and Malayalam
- [x] **🔍 Language Detection**: Automatic detection of input language using SarvamAI
- [x] **🔄 Translation**: Real-time translation from Indic languages to English
- [x] **📊 Data Analysis**: Integration with Snowflake Cortex Analyst for customer support ticket analysis
- [x] **🐛 Debug Mode**: Real-time logging and translation preview
- [ ] **📈 Monitoring**: Optional TruLens integration for agent monitoring and evaluation
- [x] **💬 Chat Interface**: User-friendly Streamlit chat interface

## Architecture

The application uses a multi-tool agent architecture:

1. **Language Identifier Tool**: Detects the language of user input
2. **Translator Tool**: Translates non-English questions to English
3. **Cortex Analyst Tool**: Processes English queries against Snowflake data

## Prerequisites

- Python 3.12 or higher
- Snowflake account with Cortex Analyst access
- SarvamAI API key
- UV package manager (recommended) or pip

## Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd linguatics-agents-demo
   ```

2. **Install dependencies using UV** (recommended):

   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   Copy `.env.example` to `.env` and configure:

   ```properties
   SNOWFLAKE_DEFAULT_CONNECTION_NAME="your-connection-name"
   PRIVATE_KEY_PASSPHRASE="your-private-key-passphrase"
   SARVAM_API_KEY="your-sarvam-api-key"
   SNOWFLAKE_USER=your-username
   SNOWFLAKE_ACCOUNT=your-account
   SNOWFLAKE_PASSWORD=your-password
   SNOWFLAKE_ROLE=your-role
   SNOWFLAKE_DATABASE=your-database
   SNOWFLAKE_WAREHOUSE=your-warehouse
   LOGGING_LEVEL=DEBUG
   ```

## Configuration

### Snowflake Setup

#### DB Setup

Ensure you have Snowflake CLI installed and configured with your account details. Preferred to have user with `ACCOUNTADMIN` role to create the required database objects, before strip down to fine-grained access control for the MCP demo.

##### Create Database Objects

> [!IMPORTANT]
> Edit the `scripts/data/support_tickets.yaml` and update the `KAMESH_MCP_DEMO` to match your DB that you will be using for the demo i.e `$SNOWFLAKE_MCP_DEMO_DATABASE`.

Run the following SQL commands in your Snowflake account to create the necessary database objects:

```shell
./scripts/setup.sh
```

##### Programmatic Access Token

We will be using a programmatic access token to authenticate with the Snowflake Cortex APIs. You can create a token by following these steps:

```shell
./scripts/pat.sh
```

Verify if the programmatic access token is created successfully and working:

```shell
 snow connection test -x \
    --user "$SA_USER" \
    --role "$SNOWFLAKE_MCP_DEMO_ROLE"
```

Verify if the service user is able to access the database objects created in the previous step:

```shell
 curl --location \
   "https://$SNOWFLAKE_ACCOUNT.snowflakecomputing.com/api/v2/databases/$SNOWFLAKE_MCP_DEMO_DATABASE/schemas/data/cortex-search-services/invoice_search_service:query" \
   --header 'X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN' \
   --header 'Content-Type: application/json' --header 'Accept: application/json' \
   --header "Authorization: Bearer $SNOWFLAKE_PASSWORD" \
    --data '{ "query": "What kind of service does Gregory have?","columns": ["CHUNK",
                "FILE_NAME"],"limit": 1}'
```

### SarvamAI Setup

1. Sign up for SarvamAI and obtain an API key
2. Add the API key to your `.env` file

## Usage

1. **Start the application**:

   ```bash
   streamlit run main.py
   ```

2. **Configure settings** in the sidebar:
   - Enable/disable TruLens monitoring
   - Toggle debug mode for detailed logging

3. **Ask questions** in your preferred language:
   - Hindi: "क्या आप मुझे सेवा प्रकार - सेल्युलर बनाम बिजनेस इंटरनेट के आधार पर ग्राहक सहायता टिकटों का विवरण दिखा सकते हैं?"
   - Tamil: "கிரிகோரி ரோமிங் கட்டணம் வசூலிக்கப்பட்டாரா?"
   - Telugu: "ఎన్ని ప్రత్యేకమైన వినియోగదారులు 'సెల్‌యులార్' సేవ రకాన్ని ఎంచుకొని, వారి సంప్రదింపు ప్రాధాన్యతగా 'ఇమెయిల్' ని ఎంచుకొని సహాయ టికెట్ను సమర్పించారు?"

4. **View results**:
   - The agent will detect the language, translate if needed, and provide analysis
   - Debug mode shows translation details and processing logs

## Sample Questions

The `samples/` directory contains example questions in various languages:

- `hindi_questions.txt` - Hindi language examples
- `tamil_questions.txt` - Tamil language examples
- `telugu_questions.txt` - Telugu language examples
- `kannada_questions.txt` - Kannada language examples
- `malayalam_questions.txt` - Malayalam language examples

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Snowflake](https://snowflake.com)
- [Snowflake Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [SarvamAI](https://sarvam.ai) for Indic language processing capabilities
- [Streamlit](https://streamlit.io) for the web application framework
- [TruLens](https://trulens.org) for agent monitoring and evaluation

---

**Note**: This is a demonstration application purpose only.
