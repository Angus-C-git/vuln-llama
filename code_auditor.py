# Pull code to be audited from a git repository to
# the fs and process it from there
import os
import git
import argparse
from rich import print
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner, SPINNERS
from rich.live import Live
from rich.console import Console

console = Console()


# we need to split the text (code) into chunks
# to be able to process it because the models
# context window
from langchain.text_splitter import Language

# load various models from the community
from langchain_community.chat_models.ollama import ChatOllama

# chunking and vectorization
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_community.document_loaders.generic import GenericLoader

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
        exclude=flags.ignore,
        parser=LanguageParser(language=LANGUAGES[flags.lang]),
        show_progress=True,
    )

    # create documents
    documents = loader.load()

    # chunk the code recursively maintaining language conventions
    splitter = RecursiveCharacterTextSplitter.from_language(
        LANGUAGES[flags.lang], chunk_size=200000, chunk_overlap=100
    )

    # create chunks
    texts = splitter.split_documents(documents)

    # seed the llm using the prompt template
    prompt = PromptTemplate.from_template(TEMPLATE)

    # init CodeLlama model
    llm = ChatOllama(model=flags.model)

    # TODO: conmbine the chunks from the same file into single
    # output to print
    file_analysis = ""
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

        # emulate chat like experience with a live feed
        with console.status(f"[b green] Analysing code from: {fname}...\n") as status:
            block = ""
            for chunk in chain.stream(
                {
                    "question": "Scan the provided code for any security flaws. Present only the most severe vulnerability found in markdown format.",
                    "code": code,
                }
            ):
                block += f"{chunk}"

            md = Markdown(block)
            console.print(Panel(md, title=f"[b green]{fname}[/b green]"), end="\n\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo", type=str, default="https://github.com/fonttools/fonttools.git"
    )
    parser.add_argument("--path", type=str, default=LOCAL_REPO_DIR)
    parser.add_argument("--model", type=str, default="mistral")
    parser.add_argument("--lang", type=str, default="python")
    parser.add_argument("--chunk-size", type=int, default=100000)
    parser.add_argument("--chunk-overlap", type=int, default=1000)
    parser.add_argument("--ignore", type=list, default=[".git"])
    args = parser.parse_args()

    print(f"[>>] Using repo: {args.repo}")
    print(f"[>>] Using model: {args.model}")
    print(f"[>>] Using language: {args.lang}")

    main(args)
