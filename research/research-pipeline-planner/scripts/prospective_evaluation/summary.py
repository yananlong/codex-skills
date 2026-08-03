from __future__ import annotations
from typing import Any
from .common import AUTHORITIES, compute_metrics, meaningful, metrics_ok, req, same

def validate_summary(ctx:dict[str,Any],obs:dict[str,Any],s:Any,profile:str,e:list[str])->None:
    p=ctx["protocol"];o=obs["observations"];complete=obs["complete"];pending=obs["pending"];excluded=obs["excluded"]
    if not isinstance(s,dict) or s.get("schema_version")!="1.0":e.append("summary schema_version must be 1.0");return
    req(s.get("study_id")==p.get("study_id") and s.get("protocol_digest")==p.get("protocol_digest",""),"summary identity mismatch",e)
    req(s.get("status") in {"draft","complete"},"summary status invalid",e);auth=s.get("conclusion_authority");req(auth in AUTHORITIES,"summary authority invalid",e)
    req(sorted(map(str,s.get("included_project_ids",[])))==sorted(str(x["project_id"]) for x in complete),"summary included IDs mismatch",e)
    req(sorted(map(str,s.get("excluded_project_ids",[])))==sorted(excluded),"summary excluded IDs mismatch",e)
    req(sorted(map(str,s.get("pending_project_ids",[])))==sorted(pending),"summary pending IDs mismatch",e)
    req(meaningful(s.get("conclusion")) and isinstance(s.get("limitations"),list) and bool(s.get("limitations")),"summary conclusion/limitations invalid",e)
    overall=compute_metrics(complete);metrics_ok(s.get("metrics"),overall,"summary.metrics",e)
    conditions={x.get("condition") for x in complete};expected={c:compute_metrics([x for x in complete if x.get("condition")==c]) for c in conditions}
    cm=s.get("condition_metrics");req(isinstance(cm,dict) and set(cm)==set(expected),"condition_metrics mismatch",e)
    if isinstance(cm,dict):
        for c,m in expected.items():metrics_ok(cm.get(c),m,f"condition_metrics.{c}",e)
    done=o.get("status")=="complete" and s.get("status")=="complete" and not pending and bool(complete)
    if auth!="instrumentation_only":req(ctx["frozen"] and done,"prospective authority requires frozen complete observations",e)
    if profile=="prospective":req(ctx["frozen"] and done and auth!="instrumentation_only","prospective profile incomplete",e)
    if auth=="prospective_descriptive":req(done,"descriptive authority incomplete",e)
    if auth in {"comparative_exploratory","comparative_confirmatory"}:
        req(p.get("design_class")=="comparative" and conditions=={"suite","comparator"},"comparative authority lacks design or conditions",e)
        suite=expected.get("suite",{});base=expected.get("comparator",{});want={}
        for t in ctx["comparison"].get("effect_thresholds",[]):
            k=t.get("endpoint_id");a=suite.get(k);b=base.get(k);effect=None if a is None or b is None else (a-b if t.get("direction")=="higher" else b-a)
            want[str(k)]={"endpoint_id":k,"suite_value":a,"comparator_value":b,"effect":effect,"threshold_met":effect is not None and effect>=t.get("minimum_effect",0)}
        got={str(x.get("endpoint_id")):x for x in s.get("comparisons",[]) if isinstance(x,dict)};req(set(got)==set(want),"comparisons do not cover frozen thresholds",e)
        for k,w in want.items():
            g=got.get(k,{})
            for f in ("suite_value","comparator_value","effect"):req(same(g.get(f),w[f]),f"comparison {k} {f} mismatch",e)
            req(g.get("threshold_met") is w["threshold_met"],f"comparison {k} threshold mismatch",e)
    informed=any(isinstance(a,dict) and a.get("outcome_informed") is True for a in ctx["amendments"])
    if auth=="comparative_confirmatory":
        req(p.get("assurance_class")=="confirmatory" and not informed,"confirmatory authority invalidated",e)
        ind=ctx["independence"];dims=set(map(str,ind.get("dimensions",[])))
        req(ind.get("self_review") is False and {"context","evaluation","advancement_authority"}<=dims,"confirmatory independence insufficient",e)
        req(all(isinstance(x,dict) and x.get("threshold_met") is True for x in s.get("comparisons",[])),"confirmatory thresholds not met",e)
