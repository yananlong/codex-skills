from __future__ import annotations
from typing import Any
from .common import ADVERSE, TERMINAL, meaningful, parse_time, req

def validate_observations(ctx:dict[str,Any],o:Any,e:list[str])->dict[str,Any]|None:
    p=ctx["protocol"]
    if not isinstance(o,dict) or o.get("schema_version")!="1.0":e.append("observations schema_version must be 1.0");return None
    req(o.get("study_id")==p.get("study_id") and o.get("protocol_version")==p.get("protocol_version"),"observation protocol identity mismatch",e)
    req(o.get("protocol_digest")==p.get("protocol_digest","") and o.get("challenge_set_digest")==ctx["custody"].get("challenge_freeze_digest","") ,"observation digest mismatch",e)
    req(o.get("status") in {"draft","in_progress","complete"},"observation status invalid",e)
    enrolled=o.get("enrolled_project_ids",[]);projects=o.get("projects",[])
    req(isinstance(enrolled,list) and len(enrolled)==len(set(map(str,enrolled))),"enrolled IDs invalid",e);req(isinstance(projects,list),"projects must be list",e)
    ids=[];complete=[];pending=[];excluded=[];freeze=parse_time(p.get("frozen_at")) if ctx["frozen"] else None
    for i,x in enumerate(projects if isinstance(projects,list) else []):
        q=f"project[{i}]";req(isinstance(x,dict),f"{q} invalid",e)
        if not isinstance(x,dict):continue
        pid=x.get("project_id");req(meaningful(pid) and pid not in ids,f"{q}.project_id invalid",e);pid=str(pid);ids.append(pid)
        req(x.get("protocol_version")==p.get("protocol_version"),f"{q} protocol version mismatch",e)
        if x.get("enrollment_status")=="excluded":
            excluded.append(pid);z=x.get("exclusion",{})
            req(isinstance(z,dict) and z.get("rule_id") in ctx["rules"] and z.get("recorded_before_outcome") is True and meaningful(z.get("rationale")) and isinstance(z.get("evidence_paths"),list) and bool(z.get("evidence_paths")),f"{q} invalid exclusion",e);continue
        req(x.get("enrollment_status")=="included",f"{q} enrollment_status invalid",e)
        cond=x.get("condition");req(cond=="suite" if p.get("design_class")=="descriptive" else cond in {"suite","comparator"},f"{q} condition invalid",e)
        req(x.get("genuinely_new") is True and x.get("implementation_tuning_access") is False,f"{q} is not prospective",e)
        oc=x.get("outcome_complete");req(isinstance(oc,bool),f"{q}.outcome_complete invalid",e)
        (complete if oc else pending).append(x if oc else pid)
        if not oc:req(o.get("status")!="complete" and x.get("final_route_state")=="unresolved",f"{q} pending state invalid",e)
        st=parse_time(x.get("started_at"));req(st is not None and (freeze is None or st>=freeze),f"{q} started before freeze or timestamp invalid",e)
        fs=x.get("final_route_state");req(fs in TERMINAL|{"unresolved"},f"{q} final state invalid",e);en=parse_time(x.get("ended_at")) if fs in TERMINAL else None
        req((fs in TERMINAL and en is not None and st is not None and en>=st) or (fs=="unresolved" and x.get("ended_at") in {"",None}),f"{q} end state invalid",e)
        req(isinstance(x.get("identity_transition_count"),int) and x["identity_transition_count"]>=0 and isinstance(x.get("late_conclusion_changing_omissions"),int) and x["late_conclusion_changing_omissions"]>=0 and isinstance(x.get("deviations"),list),f"{q} count/deviation fields invalid",e)
        events=x.get("transition_events",[]);req(isinstance(events,list),f"{q} transition_events invalid",e);seen=set()
        for a in events if isinstance(events,list) else []:
            ok=isinstance(a,dict) and meaningful(a.get("transition_id")) and a.get("transition_id") not in seen and a.get("truth_class") in {"major","nonmajor"} and a.get("alert_class") in {"major","nonmajor","none"} and a.get("adjudicated_change_class") in {"D0","D1","D2","D3","D4"} and isinstance(a.get("adjudicator_blinded"),bool)
            req(ok,f"{q} invalid transition event",e)
            if isinstance(a,dict):seen.add(a.get("transition_id"))
        visible=x.get("visible_seed_ids",[]);req(isinstance(visible,list),f"{q} visible_seed_ids invalid",e);visible=set(map(str,visible)) if isinstance(visible,list) else set()
        challenges=x.get("hidden_challenges",[]);req(isinstance(challenges,list),f"{q} hidden_challenges invalid",e);seen=set()
        for r in challenges if isinstance(challenges,list) else []:
            rid=r.get("record_id") if isinstance(r,dict) else None
            ok=isinstance(r,dict) and meaningful(rid) and rid not in seen and rid not in visible and r.get("visible_before_search") is False and isinstance(r.get("importance"),(int,float)) and r["importance"]>0 and isinstance(r.get("recovered_initially"),bool) and isinstance(r.get("recovered_after_repair"),bool) and not (r["recovered_initially"] and not r["recovered_after_repair"])
            req(ok,f"{q} invalid hidden challenge",e)
            if isinstance(r,dict):
                seen.add(rid)
                if r.get("recovered_initially") is False and r.get("recovered_after_repair") is True:req(meaningful(r.get("repair_id")),f"{q} repaired recovery lacks repair_id",e)
        outcomes=x.get("valid_scientific_outcomes",[]);req(isinstance(outcomes,list),f"{q} outcomes invalid",e);seen=set()
        for a in outcomes if isinstance(outcomes,list) else []:
            cls=a.get("outcome_class") if isinstance(a,dict) else None;rid=a.get("run_id") if isinstance(a,dict) else None
            ok=isinstance(a,dict) and meaningful(rid) and rid not in seen and cls in {"positive"}|ADVERSE and isinstance(a.get("retained_in_audit"),bool) and a.get("manuscript_disposition") in {"assert","qualify","limitation","contradict","omit"}
            req(ok,f"{q} invalid scientific outcome",e)
            if isinstance(a,dict):
                seen.add(rid)
                if cls in ADVERSE:req(a.get("retained_in_audit") is True and a.get("manuscript_disposition")!="assert",f"{q} adverse evidence hidden or asserted",e)
    req(set(map(str,enrolled))==set(ids),"every enrolled project must be accounted exactly once",e)
    if o.get("status")=="complete":req(not pending and len(complete)>=p.get("enrollment_target",0),"complete observations miss included-project target",e)
    return {"observations":o,"complete":complete,"pending":pending,"excluded":excluded}
