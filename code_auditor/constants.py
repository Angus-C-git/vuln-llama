from langchain_community.document_loaders.parsers import LanguageParser

# simplify arg switching for the loader
LANGUAGES = {
    "python": LanguageParser(language="python"),
    "javascript": LanguageParser(language="js"),
    "java": LanguageParser(language="java"),
    "go": LanguageParser(language="go"),
    "rust": LanguageParser(language="rust"),
    "c": LanguageParser(language="c"),
    "cpp": LanguageParser(language="cpp"),
}


TEMPLATE = """
Based on the code provided below answer the question.

Code: {code}

Question: {question}
"""
