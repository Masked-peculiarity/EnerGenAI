import json
from langgraph.graph import END, START, StateGraph
from app.agent.state import AgentState
from app.agent.tools import execute_tool,plan_tools,resolve_period

class EnergyAgent:
    def __init__(self,energy,rag,generator):
        self.energy,self.rag,self.generator = energy,rag,generator
        graph = StateGraph(AgentState)
        graph.add_node("route_tools",self.route)
        graph.add_node("execute_tools",self.execute)
        graph.add_node("compose",self.compose)
        graph.add_edge(START,"route_tools")
        graph.add_edge("route_tools","execute_tools")
        graph.add_edge("execute_tools","compose")
        graph.add_edge("compose",END)
        self.graph = graph.compile()

    def route(self,state):
        start,end = resolve_period(state["question"],self.energy)
        return {"tools":plan_tools(state["question"]),"start":start,"end":end}

    def execute(self,state):
        results,sources,retrieval_trace,trace = {},[],[],[]
        for name in state["tools"]:
            try:
                value = execute_tool(name,state,self.energy,self.rag)
                if name=="search_energy_knowledge":
                    sources,retrieval_trace = value["sources"],value["trace"]
                    value = {"matched_sources":len(sources),"corrective_attempts":value["attempts"]}
                results[name] = value
                trace.append({"tool":name,"status":"ok"})
            except ValueError as error:
                results[name] = {"error":str(error)}
                trace.append({"tool":name,"status":"unavailable"})
            except Exception:
                # Private persistence failure cannot make public analytics unusable.
                results[name] = {"error":"Tool temporarily unavailable"}
                trace.append({"tool":name,"status":"unavailable"})
        return {"results":results,"sources":sources,"retrieval_trace":retrieval_trace,"tool_trace":trace}

    def compose(self,state):
        lines = ["These results describe the UCI demonstration household in 2016. 'Today' and 'yesterday' refer to its latest recorded day."]
        results = state["results"]
        for name,value in results.items():
            if "error" in value:
                lines.append(f"{name}: {value['error']}")
            elif name=="get_energy_summary":
                lines.append(f"From {value['period_start']} to {value['period_end']}, appliance use totals {value['total_appliance_kwh']:.3f} kWh. The highest interval is {value['peak_interval']['appliances_wh']:.0f} Wh at {value['peak_interval']['timestamp']}.")
            elif name=="forecast_energy":
                lines.append(f"The next {value['horizon_minutes']} minutes are forecast to use {value['total_kwh']:.3f} kWh, from origin {value['origin']}. Longer-horizon forecasts are more uncertain.")
            elif name=="detect_anomalies":
                lines.append(f"There are {value['total']} unusual intervals in the selected period. These flags do not establish an appliance fault or the cause of high usage." if value["evaluated_intervals"] else "No held-out anomaly scores exist for this period; this does not mean no anomalies occurred.")
            elif name=="get_peak_usage":
                lines.append(f"The highest-use hour begins {value['peak_hour']['timestamp']} with {value['peak_hour']['appliances_wh']:.0f} Wh across {value['peak_hour']['intervals']} recorded intervals. Utility peak-price hours may differ.")
            elif name=="estimate_cost":
                lines.append(f"Estimated appliance cost: {value['estimated_cost']:.2f} in your tariff's currency." if value["estimated_cost"] is not None else "Set your tariff per kWh to calculate cost; no universal rate is assumed.")
            elif name=="estimate_carbon":
                lines.append(f"Estimated appliance emissions: {value['estimated_carbon_kg']:.3f} kg CO2." if value["estimated_carbon_kg"] is not None else "Set a region-appropriate emissions factor in kg CO2/kWh to estimate carbon.")
        for source in state["sources"]:
            lines.append(f"[{source['citation']}] {source['source']}: {source['excerpt']}")
        if not state["sources"]:
            lines.append("No sufficiently relevant document evidence was found after corrective retrieval. I cannot substantiate document-specific advice.")
        context = json.dumps({"tools":results,"sources":[{key:row.get(key) for key in ["citation","source","authority","excerpt"]} for row in state["sources"]]})
        generated = self.generator.answer(state["messages"],context)
        return {"reply":generated or "\n\n".join(lines),"mode":"ai" if generated else "local"}

    def chat(self,messages,username=None,tariff=None,factor=None):
        state = self.graph.invoke({"question":messages[-1]["content"],"messages":messages,"username":username,"tariff":tariff,"factor":factor})
        return {key:state[key] for key in ["reply","mode","sources","tool_trace","retrieval_trace"]}
