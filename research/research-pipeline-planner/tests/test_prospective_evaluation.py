#!/usr/bin/env python3
from __future__ import annotations
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(SCRIPTS))
from prospective_evaluation import ENDPOINTS,compute_metrics,protocol_digest
VALIDATOR=SCRIPTS/"validate_prospective_evaluation.py";INITIALIZER=SCRIPTS/"init_prospective_evaluation.py"

class ProspectiveTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.protocol=self.make_protocol();self.obs=self.make_obs();self.summary=self.make_summary();self.write()
    def tearDown(self):self.t.cleanup()
    def reset_state(self):
        self.protocol=self.make_protocol();self.obs=self.make_obs();self.summary=self.make_summary();self.write()
    @staticmethod
    def make_protocol(design="descriptive",assurance="exploratory"):
        p={"schema_version":"1.0","study_id":"S1","protocol_version":1,"status":"frozen","frozen_at":"2026-08-04T00:00:00+00:00","protocol_digest":"","design_class":design,"assurance_class":assurance,"primary_endpoints":["drift_sensitivity","critical_paper_recall_post_repair","adverse_evidence_retention_rate","terminal_route_rate"],"secondary_endpoints":sorted(ENDPOINTS-{"drift_sensitivity","critical_paper_recall_post_repair","adverse_evidence_retention_rate","terminal_route_rate"}),"project_eligibility":"Projects not used to tune PR16.","project_exclusion_rules":[{"rule_id":"X1","description":"Withdrawn before outcome.","frozen_before_outcome":True}],"enrollment_target":1 if design=="descriptive" else 2,"stopping_rule":"Stop at frozen target.","missing_data_policy":"Retain missingness.","technical_failure_policy":"Retain technical failures.","custody":{"challenge_custodian":"Independent custodian","challenge_freeze_digest":"a"*64,"challenge_frozen_before_search":True,"evaluator_independence":{"self_review":assurance!="confirmatory","dimensions":[] if assurance!="confirmatory" else ["context","evaluation","advancement_authority"],"evidence":"Separated review."}},"comparison":{"mode":"none" if design=="descriptive" else "parallel","comparator":"" if design=="descriptive" else "prior workflow","allocation_frozen_before_outcome":design=="comparative","equal_information_access":design=="comparative","sample_size_rule":"" if design=="descriptive" else "Frozen pilot target.","uncertainty_method":"" if design=="descriptive" else "Exact project effects.","effect_thresholds":[] if design=="descriptive" else [{"endpoint_id":"terminal_route_rate","direction":"higher","minimum_effect":0.0}]},"conclusion_policy":{"max_authority":"descriptive" if design=="descriptive" else "comparative","no_promotion_from_pilot":True,"downgrade_rules":["Outcome-informed changes downgrade authority."]},"amendments":[]}
        p["protocol_digest"]=protocol_digest(p);return p
    @staticmethod
    def project(pid="P1",condition="suite",terminal=True):
        return {"project_id":pid,"protocol_version":1,"enrollment_status":"included","condition":condition,"genuinely_new":True,"implementation_tuning_access":False,"outcome_complete":True,"started_at":"2026-08-05T00:00:00+00:00","ended_at":"2026-08-15T00:00:00+00:00" if terminal else "","transition_events":[{"transition_id":pid+"-T1","truth_class":"major","alert_class":"major","adjudicated_change_class":"D3","adjudicator_blinded":True},{"transition_id":pid+"-T2","truth_class":"nonmajor","alert_class":"nonmajor","adjudicated_change_class":"D1","adjudicator_blinded":True}],"visible_seed_ids":[pid+"-V"],"hidden_challenges":[{"record_id":pid+"-H1","importance":2.0,"visible_before_search":False,"recovered_initially":False,"recovered_after_repair":True,"repair_id":pid+"-R"},{"record_id":pid+"-H2","importance":1.0,"visible_before_search":False,"recovered_initially":True,"recovered_after_repair":True,"repair_id":""}],"late_conclusion_changing_omissions":0,"valid_scientific_outcomes":[{"run_id":pid+"-POS","outcome_class":"positive","retained_in_audit":True,"manuscript_disposition":"assert"},{"run_id":pid+"-NEG","outcome_class":"negative","retained_in_audit":True,"manuscript_disposition":"qualify"}],"final_route_state":"submit" if terminal else "unresolved","identity_transition_count":2,"deviations":[]}
    def make_obs(self,comparative=False):
        ps=[self.project()]+([self.project("P2","comparator",False)] if comparative else [])
        return {"schema_version":"1.0","study_id":"S1","protocol_version":1,"protocol_digest":self.protocol["protocol_digest"],"challenge_set_digest":"a"*64,"status":"complete","enrolled_project_ids":[x["project_id"] for x in ps],"projects":ps}
    def make_summary(self,authority="prospective_descriptive"):
        ps=[x for x in self.obs["projects"] if x["enrollment_status"]=="included" and x["outcome_complete"]];conds={x["condition"] for x in ps};cm={c:compute_metrics([x for x in ps if x["condition"]==c]) for c in conds};comps=[]
        for t in self.protocol["comparison"]["effect_thresholds"]:
            k=t["endpoint_id"];a=cm["suite"][k];b=cm["comparator"][k];z=a-b if t["direction"]=="higher" else b-a;comps.append({"endpoint_id":k,"suite_value":a,"comparator_value":b,"effect":z,"threshold_met":z>=t["minimum_effect"]})
        return {"schema_version":"1.0","study_id":"S1","protocol_digest":self.protocol["protocol_digest"],"status":"complete","conclusion_authority":authority,"included_project_ids":[x["project_id"] for x in ps],"excluded_project_ids":[],"pending_project_ids":[],"metrics":compute_metrics(ps),"condition_metrics":cm,"comparisons":comps,"conclusion":"Bounded prospective evidence.","limitations":["Project-bounded evidence only."]}
    def write(self):
        for n,x in (("prospective-protocol.json",self.protocol),("prospective-observations.json",self.obs),("prospective-summary.json",self.summary)):(self.root/n).write_text(json.dumps(x))
    def validate_pack(self,expect=0,profile="prospective"):
        r=subprocess.run([sys.executable,str(VALIDATOR),"--protocol",str(self.root/"prospective-protocol.json"),"--observations",str(self.root/"prospective-observations.json"),"--summary",str(self.root/"prospective-summary.json"),"--assurance-profile",profile],text=True,capture_output=True);self.assertEqual(r.returncode,expect,r.stdout+r.stderr);return r.stdout
    def test_valid_descriptive(self):self.validate_pack()
    def test_initializer_draft(self):
        d=self.root/"new";r=subprocess.run([sys.executable,str(INITIALIZER),str(d)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        r=subprocess.run([sys.executable,str(VALIDATOR),"--protocol",str(d/"prospective-protocol.json"),"--observations",str(d/"prospective-observations.json"),"--summary",str(d/"prospective-summary.json")],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_digest_and_metric_tampering(self):
        for mutation,needle in ((lambda:self.protocol.__setitem__("project_eligibility","changed"),"protocol_digest mismatch"),(lambda:self.summary["metrics"].__setitem__("terminal_route_rate",0),"terminal_route_rate mismatch")):
            with self.subTest(needle=needle):
                self.protocol=self.make_protocol();self.obs=self.make_obs();self.summary=self.make_summary();mutation();self.write();self.assertIn(needle,self.validate_pack(1))
    def test_nonprospective_and_leaked_challenge(self):
        cases=[(lambda p:p.__setitem__("implementation_tuning_access",True),"not prospective"),(lambda p:p["hidden_challenges"][0].__setitem__("record_id",p["visible_seed_ids"][0]),"invalid hidden challenge"),(lambda p:p["hidden_challenges"][0].__setitem__("repair_id",""),"lacks repair_id")]
        for change,needle in cases:
            with self.subTest(needle=needle):
                self.reset_state();change(self.obs["projects"][0]);self.write();self.assertIn(needle,self.validate_pack(1))
    def test_adverse_evidence_and_enrollment_accounting(self):
        self.obs["projects"][0]["valid_scientific_outcomes"][1]["retained_in_audit"]=False;self.summary=self.make_summary();self.write();self.assertIn("adverse evidence hidden",self.validate_pack(1))
        self.reset_state();self.obs["enrolled_project_ids"].append("MISSING");self.write();self.assertIn("accounted exactly once",self.validate_pack(1))
    def test_in_progress_project(self):
        p=self.obs["projects"][0];p.update(outcome_complete=False,final_route_state="unresolved",ended_at="");self.obs["status"]="in_progress";self.summary={"schema_version":"1.0","study_id":"S1","protocol_digest":self.protocol["protocol_digest"],"status":"draft","conclusion_authority":"instrumentation_only","included_project_ids":[],"excluded_project_ids":[],"pending_project_ids":["P1"],"metrics":{k:None for k in ENDPOINTS},"condition_metrics":{},"comparisons":[],"conclusion":"In progress.","limitations":["No conclusion."]};self.write();self.validate_pack(profile="structural")
    def configure_comparative(self,assurance="exploratory",authority="comparative_exploratory"):
        self.protocol=self.make_protocol("comparative",assurance);self.obs=self.make_obs(True);self.summary=self.make_summary(authority);self.write()
    def test_comparative_and_effect_derivation(self):
        self.configure_comparative();self.validate_pack();self.summary["comparisons"][0]["effect"]=99;self.write();self.assertIn("effect mismatch",self.validate_pack(1))
    def test_confirmatory_gates(self):
        for kind,needle in (("independence","independence insufficient"),("amendment","authority invalidated"),("threshold","thresholds not met")):
            with self.subTest(kind=kind):
                self.configure_comparative("confirmatory","comparative_confirmatory")
                if kind=="independence":self.protocol["custody"]["evaluator_independence"]["self_review"]=True
                elif kind=="amendment":self.protocol["amendments"]=[{"amendment_id":"A1","rationale":"post outcome","outcome_informed":True}]
                else:self.protocol["comparison"]["effect_thresholds"][0]["minimum_effect"]=2
                self.protocol["protocol_digest"]=protocol_digest(self.protocol);self.obs["protocol_digest"]=self.protocol["protocol_digest"];self.summary=self.make_summary("comparative_confirmatory");self.write();self.assertIn(needle,self.validate_pack(1))

if __name__=="__main__":unittest.main()
