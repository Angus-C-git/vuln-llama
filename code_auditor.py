# Pull code to be audited from a git repository to
# the fs and process it from there
import os
import git
import argparse

# we need to split the text (code) into chunks
# to be able to process it because the models
# context window
from langchain.text_splitter import Language

# load various models from the community
from langchain_community.chat_models import BedrockChat, ChatOllama

# chunking and vectorization
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.vectorstores import FAISS

from langchain_text_splitters import RecursiveCharacterTextSplitter

# prompting & chat experience
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


# -_-_- [TMP CONFIG] -_-_-
# REPO_URL = "https://github.com/redpointsec/vtm.git"
REPO_URL = "https://github.com/fonttools/fonttools.git"
LOCAL_REPO_DIR = "./target-repo"

from code_auditor.constants import TEMPLATE, LANGUAGES, LANGUAGE_SUFFIXES


def main(flags):
    # attempt to clone the repo to the local dir if it doesn't exist
    if not os.path.exists(flags.path):
        git.Repo.clone_from(flags.repo, flags.path)

    print(f"[>>] Repo cloned to: {flags.path}")
    print(f"[>>] Using language parser: {flags.lang}")

    # pack a loader class
    loader = GenericLoader.from_filesystem(
        flags.path,
        glob="**/*",
        suffixes=[LANGUAGE_SUFFIXES[flags.lang]],
        # ignore_dirs=[".git"],
        parser=LanguageParser(language=LANGUAGES[flags.lang]),
    )

    # create documents
    documents = loader.load()

    # chunk the code recursively maintaining language conventions
    splitter = RecursiveCharacterTextSplitter.from_language(
        LANGUAGES[flags.lang], chunk_size=100000, chunk_overlap=1000
    )

    # create chunks
    texts = splitter.split_documents(documents)

    # crate prompt template

    template = """
    Based on the code provided below answer the question.

    Code: {code}

    Question: {question}
    """

    prompt = PromptTemplate.from_template(template)

    # init CodeLlama model
    llm = ChatOllama(model_id="ollama")

    # loop through the chunks and prompt the llm to analyze it
    for text in texts:
        code = text.page_content

        # grab filename
        fname = text.metadata.get("source", "unknown")

        # crate ops chain
        chain = (
            {"code": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        # emulate chat like experience
        print(f"\n{'-_' * 10} {fname} {'-_' * 10}-")
        print(f"[>>] Analysing code from: {fname}")
        for chunk in chain.stream(
            {
                "question": "Analyze the provided code for any security flaws. Present the results in a bulleted list.",
                "code": code,
            }
        ):
            print(chunk, end="", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo", type=str, default="https://github.com/fonttools/fonttools.git"
    )
    parser.add_argument("--path", type=str, default=LOCAL_REPO_DIR)
    parser.add_argument("--model", type=str, default="ollama")
    parser.add_argument("--lang", type=str, default="python")
    args = parser.parse_args()

    print(f"[>>] Using repo: {args.repo}")
    print(f"[>>] Using model: {args.model}")
    print(f"[>>] Using language: {args.lang}")

    main(args)
