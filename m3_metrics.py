"""Operational fragility counts with explicit null/invalid/unavailable denominators."""
import copy
from m2_compare import comparison

def compare_score(results,statistic='AICc'):
    primary=comparison(results)
    if primary['status']=='NO_VALID_COMPARISON' or statistic=='AICc':return primary
    adapted=copy.deepcopy(results)
    for r in adapted:
        if r['mode']=='MLE' and r['status']=='CONVERGED':r['statistics']['AICc']=r['statistics'][statistic]
    result=comparison(adapted);result['common_AICc_eligibility_gate']=True;return result

def category(baseline,counts,thresholds):
    if baseline['status']=='NO_VALID_COMPARISON':return 'UNASSESSABLE'
    if baseline['status']=='INCONCLUSIVE':return 'INCONCLUSIVE'
    meaningful=counts['planned']-counts['not_applicable'];valid=counts['retained']+counts['flipped']+counts['to_inconclusive']
    if not meaningful or valid<thresholds['minimum_valid'] or valid/meaningful<thresholds['minimum_coverage']:return 'UNASSESSABLE'
    if counts['to_inconclusive']/valid>=thresholds['inconclusive_fraction']:return 'INCONCLUSIVE'
    if counts['retained']/valid>=thresholds['stable_persistence'] and counts['flipped']/valid<=thresholds['maximum_stable_flip_fraction']:return 'STABLE'
    return 'SENSITIVE'

def galaxy_metrics(baseline,scenarios,thresholds):
    counts={'planned':len(scenarios),'not_applicable':0,'invalid_proposal':0,'retained':0,'flipped':0,'to_inconclusive':0,'unavailable':0,'emergent_decisive':0,'baseline_nondecisive_valid_inconclusive':0}
    outcomes=[]
    for s in scenarios:
        status=s['proposal_status'];comp=s.get('comparison',{})
        if status=='NOT_APPLICABLE':outcome='not_applicable'
        elif status=='INVALID_PROPOSAL':outcome='invalid_proposal'
        elif comp['status']=='NO_VALID_COMPARISON':outcome='unavailable'
        elif baseline['status']!='PREFERENCE':outcome='emergent_decisive' if comp['status']=='PREFERENCE' else 'baseline_nondecisive_valid_inconclusive'
        elif comp['status']=='INCONCLUSIVE':outcome='to_inconclusive'
        elif comp['winner']==baseline['winner']:outcome='retained'
        else:outcome='flipped'
        counts[outcome]+=1;outcomes.append({'scenario_id':s['scenario_id'],'family':s['family'],'outcome':outcome,'comparison':comp,'failure_reasons':s.get('failure_reasons',[])})
    meaningful=counts['planned']-counts['not_applicable'];valid=counts['retained']+counts['flipped']+counts['to_inconclusive'] if baseline['status']=='PREFERENCE' else counts['emergent_decisive']+counts['baseline_nondecisive_valid_inconclusive']
    decisive=baseline['status']=='PREFERENCE'
    return {'baseline_status':baseline['status'],'baseline_winner':baseline.get('winner'),'counts':counts,'meaningful_scenarios':meaningful,'valid_comparable_scenarios':valid,'coverage':valid/meaningful if meaningful else None,'persistence_fraction':counts['retained']/valid if valid and decisive else None,'flip_fraction':counts['flipped']/valid if valid and decisive else None,'to_inconclusive_fraction':counts['to_inconclusive']/valid if valid and decisive else None,'retained_over_all_meaningful':counts['retained']/meaningful if meaningful and decisive else None,'classification':category(baseline,counts,thresholds),'outcomes':outcomes,'interpretation':'Operational fractions of a deterministic stress design; not posterior probabilities or calibrated sampling frequencies'}
