#!/usr/bin/env python3
from __future__ import annotations
import copy, json, sys, unittest
from pathlib import Path
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'; sys.path.insert(0,str(SCRIPTS))
import semantic_assurance as s

def anchor(i,d):
    x={'id':i,'definition':d}; x['definition_digest']=s.canonical_digest(x); return x

def commitment(q='Question A',obj='Object A',ev='Evidence A',paper='paper-a',version=1,cls='method',claim='Claim A',change='D0'):
    return {'schema_version':'1.0','paper_id':paper,'identity_version':version,'status':'committed','main_question':q,'central_object_or_phenomenon':obj,'contribution_class':cls,'minimum_publishable_claim':claim,'primary_evidence_obligation':ev,'intended_audience':'researchers','permitted_refinements':['narrow'],'pivot_triggers':['fatal result'],'kill_conditions':['no signal'],'successor_idea_policy':'park','next_mandatory_evidence_artifact':'results/B1.json','reconsideration_gate':'G1','selection_history':[],'predecessor_failures':[],'last_change_class':change,'last_change_rationale':'recorded','identity_anchors':{'question':anchor('Q-'+q.replace(' ','-'),q),'central_object':anchor('O-'+obj.replace(' ','-'),obj),'evidence_obligation':anchor('E-'+ev.replace(' ','-'),ev)}}

def trans(a,b,declared):
    changes=s.exact_diff(a,b); floor=s.computed_drift_floor(a,b,changes); tid='CT-1'
    t={'transition_id':tid,'from_snapshot_id':'S1','to_snapshot_id':'S2','before_digest':s.canonical_digest(a),'after_digest':s.canonical_digest(b),'declared_change_class':declared,'computed_change_class':floor,'computed_field_changes':changes,'authorization':None,'switching_cost':'','discarded_evidence':[],'successor_project_assessment':'','trigger':None}
    if declared in {'D3','D4'}:
        t.update({'trigger':{'kind':'pivot-trigger','index':0,'text':'fatal result'},'switching_cost':'cost','successor_project_assessment':'assessed','authorization':{'authorization_id':'AUTH-1','transition_id':tid,'decision':'authorize-D3' if declared=='D3' else 'close-and-create-D4','before_digest':s.canonical_digest(a),'after_digest':s.canonical_digest(b),'rationale':'authorized','self_review':True}})
    if declared=='D4':
        c={'paper_id':a['paper_id'],'identity_version':a['identity_version'],'status':'closed','before_digest':s.canonical_digest(a),'closure_rationale':'closed'}; c['closure_digest']=s.canonical_digest(c); t['old_lineage_closure']=c
    return {'schema_version':'1.0','snapshots':[{'snapshot_id':'S1','commitment':a},{'snapshot_id':'S2','commitment':b}],'transitions':[t]}

def litpack():
    perspectives=sorted(s.REQUIRED_PERSPECTIVES); qs=[]; basis=[]
    for i,p in enumerate(perspectives,1):
        qid=f'CQ-{i}'; runs=[f'RUN-{i}',f'RUN-{i}-R2']
        qs.append({'question_id':qid,'perspective':p,'priority':'high' if p in s.DEFAULT_CRITICAL_PERSPECTIVES else 'medium','critical_for_novelty':p in s.DEFAULT_CRITICAL_PERSPECTIVES,'status':'answered','search_run_ids':runs,'record_ids':['R1']})
        basis.append({'perspective':p,'applicability':'required','question_ids':[qid],'rationale':'required'})
    recs=[{'record_id':f'R{i}'} for i in range(1,6)]
    ch={'schema_version':'1.0','mode':'withheld','frozen_before_search':True,'custodian':'independent curator','challenge_records':[{'record_id':'R4','importance':2.0},{'record_id':'R5','importance':1.0}],'recovered_record_ids':['R4','R5'],'initially_missed_record_ids':[],'critical_paper_recall':1.0,'importance_weighted_recall':1.0,'search_repairs':[]}
    ch['challenge_set_digest']=s.canonical_digest(ch['challenge_records'])
    m={'schema_version':'1.1','review_profile':'bounded-systematic','records':recs,'seed_ids':['R1','R2','R3'],'coverage_questions':qs,'semantic_assurance':{'schema_version':'1.0','coverage_basis':basis,'seed_classifications':[{'record_id':'R1','classes':['foundational']},{'record_id':'R2','classes':['closest-recent']},{'record_id':'R3','classes':['competing-or-critical']}],'challenge_evaluation':{'mode':'withheld','challenge_digest':s.canonical_digest(ch)},'criticality_decisions':[],'saturation_evidence':[],'narrow_topic_exception':None}}
    n={'novelty_decision_rating':4,'top_kill_shot_objections':['R3 may subsume the claim'],'what_would_change_the_decision':'Exact subsumption lowers rating','missing_prior_work':[]}
    critical=', '.join(q['question_id'] for q in qs if q['priority']=='high')
    prior=f'# Prior-Art Matrix\n| Record ID | Work | Overlap | Threat | Surviving distinction | Coverage question IDs |\n|---|---|---|---|---|---|\n| R3 | Rival | Same target | kill-shot | Different frozen scope | {critical} |\n'
    allq=', '.join(q['question_id'] for q in qs)
    search='# Novelty Search Log\n| Run ID | Round | Query or delegation | Source | Corpus record IDs | Coverage question IDs |\n|---|---|---|---|---|---|\n'+f'| RUN-1 | 1 | direct search | db-a | R1, R2 | {allq} |\n| RUN-2 | 1 | competitor search | db-b | R3, R4 | {allq} |\n| RUN-3 | 2 | citation repair | citation | R4, R5 | {allq} |\n'
    qs[0]['search_run_ids']+=['RUN-1','RUN-2','RUN-3']
    return m,n,prior,search,ch

def dim(i,d): return {'id':i,'description':d}
def scope(i='S1',pop='POP-HELD',desc='held-out cases'):
    return {'scope_id':i,'population':dim(pop,desc),'environment':dim('ENV-V1','frozen evaluator'),'intervention':dim('INT-A','method A'),'comparator':dim('CMP-B','baseline B'),'outcomes':[dim('OUT-ACC','accuracy')],'time_or_version':dim('TIME-2026','2026 freeze'),'exclusions':[]}
def rule():
    r={'rule_id':'ER1','frozen_before_outcome':True,'description':'all measured same-scope runs'}; r['rule_digest']=s.canonical_digest(r); return r
def run_item(rid,out='positive',valid='valid',ex=None,item_class='confirmatory',block='B1'):
    rd=rule()['rule_digest']; sem={'claim_id':'C1','scope_id':'S1','eligibility_rule_id':'ER1','eligibility_rule_digest':rd,'technical_validity':valid,'outcome_class':out,'exclusion_class':ex,'complete_outcome_accounting':True,'hidden_truth_access':'blinded','material_deviations':[]}
    run={'run_id':rid,'block_id':block,'semantic_assurance':sem}
    item={'work_item_id':'WI-'+rid,'status':'completed','evidence_class':item_class,'experiment_binding':{'block_id':block},'semantic_assurance':{'claim_frozen_before_outcome':True,'decision_rule_frozen_before_outcome':True,'selection_rule_frozen_before_outcome':True,'outcome_inspected_before_freeze':False,'commitment_status_at_start':'committed','gate_frozen_at_start':True,'eligibility_rule_digests':{'ER1':rd}},'episodes':[{'experiment_run':run}]}
    src={k:sem[k] for k in ('claim_id','scope_id','eligibility_rule_id','technical_validity','outcome_class')}; src['run_id']=rid
    return item,src
def evpack(adverse=False):
    pitem,psrc=run_item('RUN-P'); items=[pitem]; src=[psrc]; disp=[]; lim=[]
    if adverse:
        nitem,nsrc=run_item('RUN-N','negative'); items.append(nitem); src.append(nsrc); disp=[{'run_id':'RUN-N','rationale':'narrows claim','manuscript_consequence':'qualify'}]; lim=['adverse run retained']
    audit={'scope_registry':[scope()],'eligibility_rules':[rule()],'audits':[{'audit_id':'A1','claim_id':'C1','scope_id':'S1','attained_assurance_class':'confirmatory','verdict':'supports_confirmatory_claim','source_runs':src,'run_selection':{'excluded_runs':[]},'adverse_evidence_dispositions':disp,'limitations':lim}]}
    paper={'scope_registry':[scope()],'claims':[{'paper_claim_id':'PC1','scope_id':'S1','evidence_mode':'empirical','manuscript_action':'qualify' if adverse else 'assert','audit_ids':['A1'],'audit_exclusions':[],'limitations':lim}]}
    blocks=[{'block_id':'B1','evidence_class':'confirmatory','selection_rule':'frozen selection','complete_outcome_accounting':'retain all outcomes','hidden_information_controls':'blinded evaluator'}]
    return audit,paper,{'items':items},blocks

class T(unittest.TestCase):
    def bad(self,errors,text): self.assertTrue(any(text in e for e in errors),errors)
    def test_d3_valid(self):
        a=commitment(); b=commitment(q='Question B',version=2,change='D3'); auth=trans(a,b,'D3'); self.assertEqual(s.validate_commitment_transitions(auth,current_commitment=b),[])
    def test_d2_cannot_hide_d3(self):
        a=commitment(); b=commitment(q='Question B',change='D2'); self.bad(s.validate_commitment_transitions(trans(a,b,'D2')),'weaker than computed drift floor')
    def test_wording_only_anchor_preserves_d0(self):
        a=commitment(); b=copy.deepcopy(a); b['main_question']='Question A, restated'; b['identity_anchors']['question']=a['identity_anchors']['question']; auth=trans(a,b,'D0'); self.assertEqual(s.validate_commitment_transitions(auth,current_commitment=b),[])
    def test_reused_authorization_fails(self):
        a=commitment(); b=commitment(q='Question B',version=2,change='D3'); c=commitment(q='Question C',version=3,change='D3'); t1=trans(a,b,'D3')['transitions'][0]; t2=trans(b,c,'D3')['transitions'][0]; t2.update(from_snapshot_id='S2',to_snapshot_id='S3',transition_id='CT-2'); t2['authorization'].update(transition_id='CT-2'); auth={'schema_version':'1.0','snapshots':[{'snapshot_id':'S1','commitment':a},{'snapshot_id':'S2','commitment':b},{'snapshot_id':'S3','commitment':c}],'transitions':[t1,t2]}; self.bad(s.validate_commitment_transitions(auth),'is reused')
    def test_current_commitment_must_match(self):
        a=commitment(); b=commitment(q='Question B',version=2,change='D3'); self.bad(s.validate_commitment_transitions(trans(a,b,'D3'),current_commitment=a),'latest transition snapshot')
    def test_stale_queued_work_fails(self):
        a=commitment(); b=commitment(q='Question B',version=2,change='D3'); wi={'items':[{'work_item_id':'W','status':'queued','paper_id':'paper-a','identity_version':1}]}; self.bad(s.validate_commitment_transitions(trans(a,b,'D3'),wi,b),'stale paper identity')
    def test_literature_valid(self): self.assertEqual(s.validate_literature_semantics(*litpack()),[])
    def test_one_seed_cannot_rating_four(self):
        v=list(litpack()); v[0]['seed_ids']=['R1']; v[0]['semantic_assurance']['seed_classifications']=v[0]['semantic_assurance']['seed_classifications'][:1]; self.bad(s.validate_literature_semantics(*v),'at least three declared seeds')
    def test_missing_perspective_fails(self):
        v=list(litpack()); v[0]['semantic_assurance']['coverage_basis'].pop(); self.bad(s.validate_literature_semantics(*v),'omits required perspectives')
    def test_withheld_seed_overlap_fails(self):
        v=list(litpack()); v[4]['challenge_records'][0]['record_id']='R1'; v[4]['challenge_set_digest']=s.canonical_digest(v[4]['challenge_records']); v[0]['semantic_assurance']['challenge_evaluation']['challenge_digest']=s.canonical_digest(v[4]); self.bad(s.validate_literature_semantics(*v),'cannot also be visible seeds')
    def test_missed_challenge_needs_repair(self):
        v=list(litpack()); v[4]['initially_missed_record_ids']=['R4']; v[0]['semantic_assurance']['challenge_evaluation']['challenge_digest']=s.canonical_digest(v[4]); self.bad(s.validate_literature_semantics(*v),'require search repair')
    def test_saturation_needs_two_rounds(self):
        v=list(litpack()); q=v[0]['coverage_questions'][0]; q['status']='saturated'; v[0]['semantic_assurance']['saturation_evidence']=[{'question_id':q['question_id'],'mode':'rounds','rounds':[{'run_id':q['search_run_ids'][0],'included_yield':1}]}]; self.bad(s.validate_literature_semantics(*v),'at least two search rounds')
    def test_empty_novelty_artifacts_fail(self):
        v=list(litpack()); v[2]='# Prior-Art Matrix\n'; v[3]='# Novelty Search Log\n'; e=s.validate_literature_semantics(*v); self.bad(e,'substantive row'); self.bad(e,'substantive query')
    def test_nonreciprocal_search_run_fails(self):
        v=list(litpack()); v[3]=v[3].replace('RUN-3','UNLINKED'); self.bad(s.validate_literature_semantics(*v),'reciprocal literature search_run_ids')
    def test_evidence_valid(self): self.assertEqual(s.validate_evidence_semantics(*evpack()),[])
    def test_adverse_valid_run_cannot_exclude(self):
        a,p,w,b=evpack(); ni,_=run_item('RUN-N','negative',ex='protocol-ineligible-configuration'); w['items'].append(ni); a['audits'][0]['run_selection']['excluded_runs']=[{'run_id':'RUN-N','eligibility_rule_id':'ER1','exclusion_class':'protocol-ineligible-configuration','evidence_paths':['failure.json'],'rationale':'exclude adverse'}]; self.bad(s.validate_evidence_semantics(a,p,w,b),'scientific outcomes cannot be excluded')
    def test_technical_failure_can_exclude(self):
        a,p,w,b=evpack(); fi,_=run_item('RUN-F','technical-failure','invalid-before-measurement','executor-failure-before-measurement'); w['items'].append(fi); a['audits'][0]['run_selection']['excluded_runs']=[{'run_id':'RUN-F','eligibility_rule_id':'ER1','exclusion_class':'executor-failure-before-measurement','evidence_paths':['failure.json'],'rationale':'failed before measurement'}]; self.assertEqual(s.validate_evidence_semantics(a,p,w,b),[])
    def test_exploratory_block_caps_assurance(self):
        a,p,w,b=evpack(); b[0]['evidence_class']='exploratory'; self.bad(s.validate_evidence_semantics(a,p,w,b),'exceeds source-derived cap')
    def test_exploratory_item_caps_assurance(self):
        a,p,w,b=evpack(); w['items'][0]['evidence_class']='exploratory'; self.bad(s.validate_evidence_semantics(a,p,w,b),'exceeds source-derived cap')
    def test_rule_digest_is_frozen(self):
        a,p,w,b=evpack(); a['eligibility_rules'][0]['description']='changed'; self.bad(s.validate_evidence_semantics(a,p,w,b),'rule_digest')
    def test_adverse_requires_qualification(self):
        a,p,w,b=evpack(True); p['claims'][0]['manuscript_action']='assert'; self.bad(s.validate_evidence_semantics(a,p,w,b),'forbids an unqualified')
    def test_scope_rewording_does_not_change_identity(self):
        a,p,w,b=evpack(); p['scope_registry'][0]['population']['description']='same population, rephrased'; self.assertEqual(s.validate_evidence_semantics(a,p,w,b),[])
    def test_duplicate_semantic_scope_ids_fail(self):
        a,p,w,b=evpack(); x=scope('S2'); a['scope_registry'].append(x); self.bad(s.validate_evidence_semantics(a,p,w,b),'semantically identical scopes')
    def test_real_fixtures(self):
        root=Path(__file__).parent/'fixtures'/'pr15'; idx=json.loads((root/'real-project-regressions.json').read_text()); self.assertEqual(s.validate_fixture_index(idx),[])
        nm=json.loads((root/'normality-milieu-transitions.json').read_text()); self.assertEqual(s.validate_commitment_transitions(nm,current_commitment=nm['snapshots'][-1]['commitment']),[]); self.assertEqual([x['computed_change_class'] for x in nm['transitions']],['D3','D2'])
        lt=json.loads((root/'llm-triangulation-transitions.json').read_text()); self.assertEqual(s.validate_commitment_transitions(lt,current_commitment=lt['snapshots'][-1]['commitment']),[]); self.assertEqual([x['computed_change_class'] for x in lt['transitions']],['D1','D2','D4'])
if __name__=='__main__': unittest.main()
