from typing import TypedDict

class AgentState(TypedDict,total=False):
    question:str
    messages:list
    username:str|None
    start:str|None
    end:str|None
    tariff:float|None
    factor:float|None
    tools:list
    results:dict
    sources:list
    retrieval_trace:list
    tool_trace:list
    reply:str
    mode:str
