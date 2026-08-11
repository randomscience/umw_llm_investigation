# UMW_LLM_investigation


## Hate List

- Luba Ślósarz - autor sekcji 10 książki
- Jakub Sojka - dyrektor Centrum Transferu Technologii UMW. - bo se wymyślił zadanie 



## Gemini api 
[basic functionality doc](https://ai.google.dev/gemini-api/docs?hl=pl#python)


[AI studio](https://aistudio.google.com/projects)


[File search doc](https://ai.google.dev/gemini-api/docs/file-search)


We should use [Gemini Embedding 2](https://ai.google.dev/gemini-api/docs/embeddings)

[LangSmith](https://eu.smith.langchain.com/o/db948735-2d39-445e-81fa-063a23107746/projects/p/ceec4fe3-3605-4029-86c7-ea8036ddc761?timeModel=%7B%22duration%22%3A%221d%22%7D)


# TODO
1. Cache vector_store [IN MEMORY VECTOR STORE] -> 
2. LLM Model ERRORS handling: 
   1. No mony left - no tokens 
   2. Rate limit exceeded error
3. Error logging 
4. Access token validation with request -> add header 
5. Support prompt_context passed by user -> define struct correctly, parse input from user, pass to model
6. Support for response languages -> from user param <low priority> 
7. Docker and hosting
8. Mock endpoint returning some answer in markdown
9. add missing libraries to .requirements
10. Parse model output and isolate "path: str  # <rozdział>/<name>.html  eg. "10/0014.html"" and "ids_to_highlight: List[str]  # ["item31989"] can be empty" 
11. find a way to make 'prompt' dumber and quicker

# 
11. Improve how frontend looks 
