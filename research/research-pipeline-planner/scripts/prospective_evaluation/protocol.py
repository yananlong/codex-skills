from __future__ import annotations
from typing import Any
from .common import ENDPOINTS, meaningful, parse_time, protocol_digest, req

def validate_protocol(p:Any,e:list[str])->dict[str,Any]|None:
    if not isinstance(p,dict) or p.get("schema_version")!="1.0":e.append("protocol schema_version must be 1.0");return None
    for k in ("study_id","project_eligibility","stopping_rule","missing_data_policy","technical_failure_policy"):req(meaningful(p.get(k)),f"protocol.{k} required",e)
    req(p.get("status") in {"draft","frozen"},"protocol.status invalid",e);frozen=p.get("status")=="frozen"
    req(p.get("design_class") in {"descriptive","comparative"},"protocol.design_class invalid",e)
    req(p.get("assurance_class") in {"exploratory","confirmatory"},"protocol.assurance_class invalid",e)
    req(isinstance(p.get("protocol_version"),int) and p["protocol_version"]>0,"protocol_version invalid",e)
    req(isinstance(p.get("enrollment_target"),int) and p["enrollment_target"]>0,"enrollment_target invalid",e)
    req(isinstance(p.get("primary_endpoints"),list) and p["primary_endpoints"] and set(p["primary_endpoints"])<=ENDPOINTS,"primary_endpoints invalid",e)
    req(isinstance(p.get("secondary_endpoints"),list) and set(p["secondary_endpoints"])<=ENDPOINTS,"secondary_endpoints invalid",e)
    if frozen:
        req(parse_time(p.get("frozen_at")) is not None,"frozen_at invalid",e);req(p.get("protocol_digest")==protocol_digest(p),"protocol_digest mismatch",e)
    else:req(p.get("protocol_digest") in {"",None},"draft protocol cannot claim digest",e)
    rules={};req(isinstance(p.get("project_exclusion_rules"),list),"project_exclusion_rules must be list",e)
    for r in p.get("project_exclusion_rules",[]):
        ok=isinstance(r,dict) and meaningful(r.get("rule_id")) and meaningful(r.get("description")) and r.get("frozen_before_outcome") is True and r.get("rule_id") not in rules
        req(ok,"invalid or duplicate exclusion rule",e)
        if isinstance(r,dict):rules[r.get("rule_id")]=r
    custody=p.get("custody",{});req(isinstance(custody,dict),"custody required",e)
    if frozen:
        req(meaningful(custody.get("challenge_custodian")),"challenge custodian required",e);d=custody.get("challenge_freeze_digest")
        req(isinstance(d,str) and len(d)==64 and set(d)<=set("0123456789abcdef"),"challenge digest invalid",e);req(custody.get("challenge_frozen_before_search") is True,"challenge must freeze before search",e)
    ind=custody.get("evaluator_independence",{});req(isinstance(ind,dict) and isinstance(ind.get("self_review"),bool) and isinstance(ind.get("dimensions"),list),"evaluator independence invalid",e)
    comp=p.get("comparison",{});req(isinstance(comp,dict),"comparison required",e)
    if p.get("design_class")=="descriptive":req(comp.get("mode")=="none","descriptive comparison.mode must be none",e)
    else:
        req(comp.get("mode") in {"parallel","matched","stepped-wedge"},"comparative mode invalid",e)
        for k in ("comparator","sample_size_rule","uncertainty_method"):req(meaningful(comp.get(k)),f"comparison.{k} required",e)
        req(comp.get("allocation_frozen_before_outcome") is True and comp.get("equal_information_access") is True,"comparative allocation/information not frozen",e)
        th=comp.get("effect_thresholds");req(isinstance(th,list) and bool(th),"effect_thresholds required",e);seen=set()
        for x in th if isinstance(th,list) else []:
            ok=isinstance(x,dict) and x.get("endpoint_id") in p.get("primary_endpoints",[]) and x.get("endpoint_id") not in seen and x.get("direction") in {"higher","lower"} and isinstance(x.get("minimum_effect"),(int,float)) and x["minimum_effect"]>=0
            req(ok,"invalid effect threshold",e)
            if isinstance(x,dict):seen.add(x.get("endpoint_id"))
    cp=p.get("conclusion_policy",{});want="descriptive" if p.get("design_class")=="descriptive" else "comparative"
    req(isinstance(cp,dict) and cp.get("max_authority")==want and cp.get("no_promotion_from_pilot") is True and isinstance(cp.get("downgrade_rules"),list) and bool(cp.get("downgrade_rules")),"conclusion_policy invalid",e)
    amendments=p.get("amendments",[]);req(isinstance(amendments,list),"amendments must be list",e)
    for a in amendments if isinstance(amendments,list) else []:req(isinstance(a,dict) and meaningful(a.get("amendment_id")) and meaningful(a.get("rationale")) and isinstance(a.get("outcome_informed"),bool),"invalid amendment",e)
    return {"protocol":p,"frozen":frozen,"rules":rules,"custody":custody,"independence":ind,"comparison":comp,"amendments":amendments}
