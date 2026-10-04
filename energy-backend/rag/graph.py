import json
import re
from typing import TypedDict
import faiss
import joblib
import numpy as np
from langgraph.graph import END, START, StateGraph
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS,TfidfVectorizer
from rag.ingest import INDEX_DIR

class RetrievalState(TypedDict,total=False):
    query:str
    original_query:str
    username:str|None
    attempts:int
    candidates:list
    sources:list
    trace:list

def tokens(text):
    return {word for word in re.findall(r"[a-z]+",text.lower()) if len(word)>2 and word not in ENGLISH_STOP_WORDS}

def rewrite_query(query):
    lower = query.lower()
    rules = {"hvac":"heating cooling thermostat filters", "ac":"heating cooling thermostat filters",
             "bulb":"lighting LED efficiency", "charge":"electricity tariff cost bill", "bill":"electricity tariff cost bill",
             "spike":"unusual appliance consumption high efficiency", "high":"reduce appliance consumption efficiency",
             "save":"reduce household energy efficiency", "reduce":"household energy efficiency heating lighting",
             "co2":"carbon grid emissions factor", "fault":"unusual consumption dataset appliance fault"}
    additions = [value for key,value in rules.items() if re.search(rf"\b{key}\b",lower)]
    return (query+" "+" ".join(additions))[:1000]

class CorrectiveRAG:
    def __init__(self,store,index_dir=INDEX_DIR):
        self.store = store
        self.index = faiss.read_index(str(index_dir/"energy.faiss"))
        self.vectorizer = joblib.load(index_dir/"vectorizer.pkl")
        self.documents = json.loads((index_dir/"chunks.json").read_text(encoding="utf-8"))
        graph = StateGraph(RetrievalState)
        graph.add_node("retrieve",self.retrieve)
        graph.add_node("grade",self.grade)
        graph.add_node("rewrite",self.rewrite)
        graph.add_edge(START,"retrieve")
        graph.add_edge("retrieve","grade")
        graph.add_conditional_edges("grade",lambda state:"rewrite" if not state["sources"] and state["attempts"]<1 else "done",{"rewrite":"rewrite","done":END})
        graph.add_edge("rewrite","retrieve")
        self.graph = graph.compile()

    def retrieve(self,state):
        query = state["query"]
        vector = self.vectorizer.transform([query]).toarray().astype("float32")
        faiss.normalize_L2(vector)
        scores,ids = self.index.search(vector,5)
        found = [{**self.documents[int(index)],"score":float(score),"section":int(index)+1,"private":False}
                 for score,index in zip(scores[0],ids[0]) if index>=0 and score>0]
        if state.get("username"):
            chunks = self.store.chunks(state["username"])
            if chunks:
                # Private corpus is constructed only from the authenticated user's rows.
                transform = TfidfVectorizer(stop_words="english",max_features=4096,dtype=np.float32)
                try:
                    vectors = transform.fit_transform([row["content"] for row in chunks]).toarray()
                    faiss.normalize_L2(vectors)
                    index = faiss.IndexFlatIP(vectors.shape[1]); index.add(vectors)
                    private_query = transform.transform([query]).toarray().astype("float32")
                    faiss.normalize_L2(private_query)
                    p_scores,p_ids = index.search(private_query,min(5,len(chunks)))
                    for score,position in zip(p_scores[0],p_ids[0]):
                        if position>=0 and score>0:
                            row = chunks[int(position)]
                            found.append({"source":row["source_name"],"authority":"User-uploaded; not independently verified",
                                "url":None,"page":None,"topic":"personal_document","document_type":"user_upload",
                                "content":row["content"][:1400],"section":row["chunk_index"]+1,"score":float(score),"private":True})
                except ValueError:
                    pass
        return {"candidates":sorted(found,key=lambda row:row["score"],reverse=True)[:8],
                "trace":[*state.get("trace",[]),{"stage":"retrieve","query":query,"candidates":len(found)}]}

    def grade(self,state):
        query_tokens = tokens(state["query"])
        accepted = [row for row in state["candidates"] if row["score"]>=.08 and query_tokens & tokens(row["content"])]
        sources = [{**row,"citation":f"S{index}","excerpt":row["content"][:900]} for index,row in enumerate(accepted[:5],1)]
        return {"sources":sources,"trace":[*state["trace"],{"stage":"grade","accepted":len(sources),"method":"TF-IDF cosine and content overlap"}]}

    def rewrite(self,state):
        rewritten = rewrite_query(state["query"])
        return {"query":rewritten,"attempts":state["attempts"]+1,
                "trace":[*state["trace"],{"stage":"rewrite","query":rewritten}]}

    def search(self,query,username=None):
        return self.graph.invoke({"query":query,"original_query":query,"username":username,"attempts":0,"trace":[]})
