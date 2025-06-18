import os

from agent_gateway.tools.logger import gateway_logger
from sarvamai import SarvamAI

SARVAM_AI_TRANSLATE_MODEL = "sarvam-translate:v1"

sarvam_api_key = os.getenv("SARVAM_API_KEY")

if not sarvam_api_key:
    raise ValueError("SARVAM_API_KEY environment variable is not set.")

__client = SarvamAI(api_subscription_key=sarvam_api_key)


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


def lang_detect(question: str) -> str | None:
    """
    Detect the language of the given question text using SarvamAI's language identification service.

    This function uses the SarvamAI client to identify the language of the input text and logs
    the detected language code for debugging purposes.

    Args:
        question (str): The input text/question for which to detect the language.

    Returns:
        str | None: The detected language code (e.g., 'en', 'hi', 'ta', etc.) or None if detection fails.

    Example:
        >>> # Detect language of English text
        >>> lang_code = lang_detect("What is the weather today?")
        >>> print(lang_code)
        'en-IN'

        >>> # Detect language of Tamil text
        >>> lang_code = lang_detect("இன்று வானிலை எப்படி இருக்கிறது?")
        >>> print(lang_code)
        'ta-IN'

        >>> # Detect language of Hindi text
        >>> lang_code = lang_detect("आज मौसम कैसा है?")
        >>> print(lang_code)
        'hi-IN'
    """
    response = __client.text.identify_language(input=question)
    __lang_code = response.language_code
    gateway_logger.log("DEBUG", f"Detected Language Code: {__lang_code}\n")

    return __lang_code


def translate(
    lang_code: str,
    question: str,
) -> str:
    """
    Translate text from a detected language to English using SarvamAI's translation service.

    This function takes a language code and question text, logs the translation process,
    and returns the English translation using the SarvamAI translation API.

    Args:
        lang_code (str): The source language code (e.g., 'hi-IN', 'ta-IN', 'te-IN').
        question (str): The input text/question to be translated to English.

    Returns:
        str: The translated text in English.

    Example:
        >>> # Translate Hindi text to English
        >>> hindi_text = "आज मौसम कैसा है?"
        >>> english_translation = translate("hi-IN", hindi_text)
        >>> print(english_translation)
        'How is the weather today?'

        >>> # Translate Tamil text to English
        >>> tamil_text = "இன்று வானிலை எப்படி இருக்கிறது?"
        >>> english_translation = translate("ta-IN", tamil_text)
        >>> print(english_translation)
        'How is the weather today?'

        >>> # Translate Telugu text to English
        >>> telugu_text = "ఈరోజు వాతావరణం ఎలా ఉంది?"
        >>> english_translation = translate("te-IN", telugu_text)
        >>> print(english_translation)
        'How is the weather today?'
    """
    gateway_logger.log(
        "DEBUG",
        f"""\n
Identified Language Code: {lang_code} \n
Question: {question}\n""",
    )

    response = __client.text.translate(
        input=question,
        source_language_code=lang_code,
        target_language_code="en-IN",
        model=SARVAM_AI_TRANSLATE_MODEL,
    )
    translation = response.translated_text
    gateway_logger.log("DEBUG", f"Translation:{translation}\n")
    return translation


def answer_translator(
    answer: str,
    lang_code: str,
) -> str:
    """
    Translate an English answer back to the original language using SarvamAI's translation service.

    This function takes an English answer and translates it back to the specified target language,
    logging the process for debugging purposes. It's typically used to translate responses back
    to the user's original language after processing.

    Args:
        lang_code (str): The target language code to translate to (e.g., 'hi-IN', 'ta-IN', 'te-IN').
        answer (str): The English text/answer to be translated to the target language.

    Returns:
        str: The translated text in the target language.

    Example:
        >>> # Translate English answer to Hindi
        >>> english_answer = "The weather today is sunny and warm."
        >>> hindi_translation = answer_translator("hi-IN", english_answer)
        >>> print(hindi_translation)
        'आज का मौसम धूप और गर्म है।'

        >>> # Translate English answer to Tamil
        >>> english_answer = "Your support ticket has been resolved."
        >>> tamil_translation = answer_translator("ta-IN", english_answer)
        >>> print(tamil_translation)
        'உங்கள் ஆதரவு டிக்கெட் தீர்க்கப்பட்டது।'

        >>> # Translate English answer to Telugu
        >>> english_answer = "Thank you for your inquiry."
        >>> telugu_translation = answer_translator("te-IN", english_answer)
        >>> print(telugu_translation)
        'మీ విచారణకు ధన్యవాదాలు।'
    """
    gateway_logger.log("DEBUG", f"English answer: \n{answer}\n")
    response = __client.text.translate(
        input=answer,
        source_language_code="en-IN",
        target_language_code=lang_code,
        mode="modern-colloquial",
        model="mayura:v1",
    )
    translation = response.translated_text
    gateway_logger.log("DEBUG", f"Translation:{translation}\n")
    return translation
