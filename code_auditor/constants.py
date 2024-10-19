from langchain_community.document_loaders.parsers import LanguageParser

# we need to split the text (code into chunks
# to be able to process it because the models
# context window
from langchain.text_splitter import Language

# simplify arg switching for the loader
# by wrapping the Language enum
LANGUAGES = {
    "python": Language.PYTHON,
    "js": Language.JS,
    "ts": Language.TS,
    "java": Language.JAVA,
    "go": Language.GO,
    "rust": Language.RUST,
    "c": Language.C,
    "cpp": Language.CPP,
}

LANGUAGE_SUFFIXES = {
    "python": ".py",
    "js": ".js",
    "ts": ".ts",
    "java": ".java",
    "go": ".go",
    "rust": ".rs",
    "c": ".c",
    "cpp": ".cpp",
}


TEMPLATE = """
    Based on the code provided below answer ONLY the question in a bulleted list. Do not provide any other text, explanation or analysis.

    Code: {code}

    Question: {question}
"""
