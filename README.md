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
- [ ] Support prompt_context passed by user -> define struct correctly, parse input from user, pass to model
- [x] Cache vector_store [IN MEMORY VECTOR STORE] -> 
- [ ] LLM Model ERRORS handling: 
   - [ ] No mony left - no tokens 
   - [x] Rate limit exceeded error - this should be done on a user level 
- [x] Error logging 
- [x] Access token validation with request -> add header 
- [x] Support for response languages -> from user param <low priority> 
- [x] Docker and hosting
- [ ] Mock endpoint returning some answer in markdown
- [x] add missing libraries to .requirements
- [ ] Parse model output and isolate "path: str  # <rozdział>/<name>.html  eg. "10/0014.html"" and "ids_to_highlight: List[str]  # ["item31989"] can be empty" 
- [x] find a way to make 'prompt' dumber and quicker

# 
11. Improve how frontend looks
