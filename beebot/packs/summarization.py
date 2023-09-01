SUMMARIZATION_TEMPLATE = """Make the following text more concise, ensuring the final output is no more than {filter_threshold} characters long.

Simplify the language used. Replace long phrases with shorter synonyms, remove unnecessary adverbs and adjectives, or rephrase sentences to make them more concise.
 
Remove redundancies, especially those written informally or conversationally, using repetitive information or phrases.

Flatten text that includes nested hierarchical information that isn't crucial for understanding.

Extract text content out of HTML tags.

Retain key details such as file names, IDs, people, places, and important events:

{long_text}"""


def _filter_long_documents(self, document: str) -> str:
    # TODO: Configurable limit or like configurable turn it off?
    if len(document) > 1000:
        summary_prompt = SUMMARIZATION_TEMPLATE.format(
            long_text=document[:8000], filter_threshold=self.filter_threshold
        )
        summarization = call_llm(summary_prompt, llm=self.llm)
        return f"The response was summarized as: {summarization}"

    return document


async def afilter_long_documents(
    self,
    document: str,
    llm: Callable[[str], str],
    allm: Callable[[str], Awaitable[str]],
) -> str:
    pass
