def get_prompt(query, retrieved, language):
    context = "\n\n".join(
        f"""
    SOURCE: {doc['file']}#{doc['div_id']}

    {doc['text']}
    """
        for doc in retrieved
    )

    prompt = f"""
    Answer the question using only the provided sources.

    The language to use is {language}

    If the information is not present in the sources,
    say that you don't know.

    Question:
    {query}

    Sources:
    {context}

    At the end, provide the source locations you used.
    """
    return prompt
