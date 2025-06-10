# Linguatics Agents Demo

A [Streamlit](https://streamlit.io) application demonstrating the use of Snowflake Cortex Analyst with Indic languages, featuring automatic language detection and translation capabilities powered by [SarvamAI](https://sarvam.ai).

This demo leverages Snowflake's [Orchestration Framework](https://github.com/snowflake-labs/orchestration-framework) to build sophisticated multilingual AI agents capable of analyzing customer support tickets across various Indic languages. The orchestration framework provides a powerful foundation for creating agentic AI workflows that can handle complex multi-step processes, tool integrations, and state management.

Key orchestration capabilities utilized in this demo:

- **Multi-tool Coordination**: Seamlessly orchestrates language detection, translation, and data analysis tools
- **Workflow Management**: Handles complex agent workflows with proper error handling and state transitions
- **Tool Integration**: Provides standardized interfaces for integrating external APIs (SarvamAI) with Snowflake services
- **Async Processing**: Supports non-blocking operations for better user experience
- **Agent Gateway**: Utilizes Snowflake's native agent orchestration capabilities for scalable deployment

This architecture ensures a seamless user experience for non-English speakers while maintaining the flexibility to extend functionality and integrate additional tools as needed.

## Overview

This demo showcases how to build multilingual AI agents that can:

- Detect the language of user questions in various Indic languages
- Translate questions to English for processing by Snowflake Cortex Analyst
- Provide responses to customer support ticket analysis queries
- Support debugging and monitoring with optional TruLens integration

## Features

- **🌐 Multilingual Support**: Supports multiple Indic languages including Hindi, Tamil, Telugu, Kannada, and Malayalam
- **🔍 Language Detection**: Automatic detection of input language using SarvamAI
- **🔄 Translation**: Real-time translation from Indic languages to English
- **📊 Data Analysis**: Integration with Snowflake Cortex Analyst for customer support ticket analysis
- **🐛 Debug Mode**: Real-time logging and translation preview
- **📈 Monitoring**: Optional TruLens integration for agent monitoring and evaluation
- **💬 Chat Interface**: User-friendly Streamlit chat interface

## Architecture

The application uses a multi-tool agent architecture:

1. **Language Identifier Tool**: Detects the language of user input
2. **Translator Tool**: Translates non-English questions to English
3. **Cortex Analyst Tool**: Processes English queries against Snowflake data

## Prerequisites

- Python 3.11 or higher
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

**TODO**: Replace this section with the actual Snowflake setup instructions, including sample data load and semantic model configuration.

1. Ensure your Snowflake account has access to Cortex Analyst
2. Set up the semantic model file (`support_tickets_semantic_model.yaml`)
3. Upload the semantic model to your Snowflake stage (`MY_MODELS`)

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
   - Hindi: "ग्राहक सहायता टिकट की स्थिति क्या है?"
   - Tamil: "வாடிக்கையாளர் ஆதரவு டிக்கெட்டின் நிலை என்ன?"
   - Telugu: "కస్టమర్ సపోర్ట్ టికెట్ స్థితి ఏమిటి?"

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

## Development

### Project Structure

```
├── main.py                 # Main Streamlit application
├── pyproject.toml         # Project configuration
├── .env                   # Environment variables (create from .env.example)
├── LICENSE                # Apache License v2.0
├── README.md             # This file
├── samples/              # Sample questions in various languages
│   ├── hindi_questions.txt
│   ├── tamil_questions.txt
│   └── ...
└── work/                 # Development notebooks
    └── Quickstart.ipynb
```

### Key Components

- **SarvamLanguageTools**: Handles language detection and translation
- **StreamlitLogHandler**: Custom logging handler for real-time log display
- **Agent Gateway Integration**: Uses Snowflake's orchestration framework
- **Async Processing**: Handles long-running agent calls without blocking UI

### Adding New Languages

To add support for new languages:

1. Ensure SarvamAI supports the language
2. Add sample questions to the `samples/` directory
3. Test language detection and translation accuracy

## Optional Features

### TruLens Integration

Enable monitoring and evaluation:

1. Install TruLens dependencies:

   ```bash
   uv sync --group trulens
   ```

2. Enable TruLens in the sidebar settings

3. Access the TruLens dashboard at `http://localhost:8084`

## Troubleshooting

### Common Issues

1. **Session State Errors**:
   - Ensure all required environment variables are set
   - Restart the Streamlit application

2. **Translation Errors**:
   - Verify SarvamAI API key is valid
   - Check network connectivity

3. **Snowflake Connection Issues**:
   - Verify connection parameters in `.env`
   - Ensure proper database/schema/warehouse access

4. **Async Context Issues**:
   - The application handles async agent calls properly
   - Check logs for detailed error information

### Debug Mode

Enable debug mode in the sidebar to see:

- Detected source language
- Translation results
- Detailed processing logs
- Agent execution steps

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Snowflake](https://snowflake.com)
- [Snowflake Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [SarvamAI](https://sarvam.ai) for Indic language processing capabilities
- [Streamlit](https://streamlit.io) for the web application framework
- [TruLens](https://trulens.org) for agent monitoring and evaluation

## Support

For questions and support:

- Open an issue in this repository
- Check the troubleshooting section above
- Review the sample notebooks in the `work/` directory

---

**Note**: This is a demonstration application purpose only.
