# Trusted energy guidance corpus

guidance.json contains six concise manually curated paraphrases,not downloaded full publications or a complete appliance-manual database.

Sources: ENERGY STAR heating/cooling and home improvements,DOE LED basics,EPA emissions methodology,UCI dataset,and internal tariff/forecast formulas. Each item records source,authority,URL/topic/type/page/content. HTML page metadata is null. Original source links were checked during implementation on3October2026.

Run python -m rag.ingest from backend to build TF-IDF/FAISS artifacts in rag/index. Startup loads existing artifacts only. Retrieval grading is cosine/content-overlap,with bounded energy query rewrite when weak. It is lexical,not transformer semantic retrieval or certified factual validation.

Private user documents are separately owner-scoped and marked unverified; no private data is baked into this shared public index. Expand corpus with attributed local tariff documents/manuals when authorized; retain metadata and evaluate source relevance.
