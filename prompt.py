def get_prompt(query, retrieved, language):
    context = "\n\n".join(
        f"""
    SOURCE: {doc['file']}#{doc['div_id']}

    {doc['text']}
    """
        for doc in retrieved
    )

    prompt = f"""
    Answer the question using only the provided exerts from the book and previous conversation context.

    The language to use is {language}

    If the information is not present in the sources, answer "Nie mogę znaleźć informacji na ten temat w książce"

    Question:
    {query}

    Sources:
    {context}
    """
    print(prompt)
    return prompt
