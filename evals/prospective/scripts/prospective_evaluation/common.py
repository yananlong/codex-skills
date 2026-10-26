from __future__ import annotations
import hashlib, json, math, statistics
from datetime import datetime
from typing import Any

ENDPOINTS={"drift_sensitivity","drift_false_positive_rate","critical_paper_recall_initial","critical_paper_recall_post_repair","importance_weighted_recall_post_repair","search_repair_gain","late_omission_rate","adverse_evidence_retention_rate","terminal_route_rate","median_days_to_terminal","median_identity_transitions_to_terminal"}
TERMINAL={"execute","submit","split","park","kill"}; ADVERSE={"negative","null","contradictory"}
AUTHORITIES={"instrumentation_only","prospective_descriptive","comparative_exploratory","comparative_confirmatory"}

def meaningful(x:Any)->bool:return isinstance(x,str) and bool(x.strip())
def canonical_digest(x:Any)->str:return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def protocol_digest(p:dict[str,Any])->str:return canonical_digest({k:v for k,v in p.items() if k!="protocol_digest"})
def rate(a:int,b:int)->float|None:return None if b==0 else a/b
def median(xs:list[float])->float|None:return None if not xs else float(statistics.median(xs))
def same(a:Any,b:Any)->bool:
    if a is None or b is None:return a is None and b is None
    return isinstance(a,(int,float)) and math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-12)
def parse_time(x:Any)->datetime|None:
    try:
        d=datetime.fromisoformat(str(x).replace("Z","+00:00"));return d if d.tzinfo else None
    except ValueError:return None
def req(ok:bool,msg:str,e:list[str])->None:
    if not ok:e.append(msg)
def metrics_ok(actual:Any,expected:dict[str,float|None],label:str,e:list[str])->None:
    req(isinstance(actual,dict) and set(actual)==ENDPOINTS,f"{label} must contain exactly supported endpoints",e)
    if isinstance(actual,dict):
        for k,v in expected.items():req(same(actual.get(k),v),f"{label}.{k} mismatch",e)

def compute_metrics(projects:list[dict[str,Any]])->dict[str,float|None]:
    maj=hit=non=fp=ct=ci=cp=late=adv=ret=term=0;wt=wp=0.0;days=[];trans=[]
    for p in projects:
        for x in p.get("transition_events",[]):
            if x.get("truth_class")=="major":maj+=1;hit+=x.get("alert_class")=="major"
            elif x.get("truth_class")=="nonmajor":non+=1;fp+=x.get("alert_class")=="major"
        for x in p.get("hidden_challenges",[]):
            ct+=1;i=x.get("recovered_initially") is True;q=x.get("recovered_after_repair") is True;ci+=i;cp+=q
            w=float(x.get("importance",0)) if isinstance(x.get("importance"),(int,float)) else 0;wt+=w;wp+=w if q else 0
        late+=int(p.get("late_conclusion_changing_omissions",0)>0)
        for x in p.get("valid_scientific_outcomes",[]):
            if x.get("outcome_class") in ADVERSE:adv+=1;ret+=x.get("retained_in_audit") is True
        if p.get("final_route_state") in TERMINAL:
            term+=1;s=parse_time(p.get("started_at"));q=parse_time(p.get("ended_at"))
            if s and q:days.append((q-s).total_seconds()/86400)
            if isinstance(p.get("identity_transition_count"),(int,float)):trans.append(float(p["identity_transition_count"]))
    n=len(projects);ir=rate(ci,ct);pr=rate(cp,ct)
    return {"drift_sensitivity":rate(hit,maj),"drift_false_positive_rate":rate(fp,non),"critical_paper_recall_initial":ir,"critical_paper_recall_post_repair":pr,"importance_weighted_recall_post_repair":None if wt==0 else wp/wt,"search_repair_gain":None if ir is None or pr is None else pr-ir,"late_omission_rate":rate(late,n),"adverse_evidence_retention_rate":rate(ret,adv),"terminal_route_rate":rate(term,n),"median_days_to_terminal":median(days),"median_identity_transitions_to_terminal":median(trans)}
