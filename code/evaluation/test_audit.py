"""Authored behavioral regressions, independent of public expected outputs."""
import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit.core import AuditEngine, Observation, IdentityIndex, case_key, deletion_intent, scalars
from audit.ingestion import log_fields, record_state, media_context
from audit.layout import resource_regions


def engine():
    e = AuditEngine.__new__(AuditEngine)
    e.identities = SimpleNamespace(resolve=lambda email: 'subject', match=lambda data:set())
    e.rules = {k:{'required_action':v} for k,v in
               [('USER_PROFILE','DELETE'),('SEARCH_INDEX_ENTRY','DELETE'),
                ('SECURITY_AUDIT_LOG','RETAIN'),('ACCOUNT_TOMBSTONE','REDACT'),
                ('ANALYTICS_PROFILE','ANONYMIZE'),('SUPPORT_MESSAGE','REDACT')]}
    e.activities=[];e.observations=[];e.snapshots=[];e.resource_links=defaultdict(list)
    e.by_resource=defaultdict(list);e.source_subjects=defaultdict(set);e.source_resources=defaultdict(set)
    e.diagnostics=[];e.sources={}
    e.relationships=[]
    return e


def add(e, resource, category, state, time='2026-01-01T00:00:00Z', scope='service', system='system'):
    evidence='source_'+str(len(e.observations)+1)
    e.sources[evidence]=time
    e.add(Observation(system,resource,category,state,time,time,evidence,scope,links={'subject'}))


def run(e, text='Please delete my account'):
    return e.audit(dict(case_id='authored',email='alias@example.test',request_text=text,
                        audit_at='2026-02-01T00:00:00Z',reported_at='2026-01-02T00:00:00Z'))


def request(start='2026-01-01T00:00:00Z', reported='2026-01-20T00:00:00Z'):
    return dict(case_id='synthetic',email='alias@example.test',request_text='Delete my account',
                requested_at=start,reported_at=reported,audit_at='2026-02-01T00:00:00Z')


def worker(resource, result='FAILED', time='2026-01-10T00:00:00Z'):
    return dict(source_system='deletion_worker',target_system='account_service',resource_id=resource,
                event_type='DELETE_RECORD',event_time=time,reported_result=result,activity_id='worker_event')


class AuditRegressions(unittest.TestCase):
    def test_case_ids_sort_numerically(self):
        self.assertEqual(sorted(['case_100','case_33','case_9'],key=case_key),['case_9','case_33','case_100'])

    def test_authorization_negation(self):
        e=engine();add(e,'account_example','USER_PROFILE','PRESENT')
        r=run(e,"Please export my data; don't delete anything")
        self.assertEqual((r['deletion_status'],json.loads(r['steps_json'])),('NOT_APPLICABLE',[]))

    def test_stop_writer_before_record_deletion(self):
        e=engine();add(e,'search_example','SEARCH_INDEX_ENTRY','PRESENT')
        add(e,'flow_example','DATA_FLOW','ACTIVE')
        r=run(e);steps=json.loads(r['steps_json'])
        self.assertEqual(r['deletion_status'],'INCOMPLETE')
        actions=[s['operation'] for s in steps if s['phase']=='REMEDIATION']
        self.assertEqual(actions,['DISABLE_DATA_FLOW','DELETE_RECORD'])
        self.assertTrue(all(s['evidence_id']=='' for s in steps if s['phase']!='FINDING'))

    def test_compliant_retention_and_tombstone(self):
        e=engine();add(e,'tombstone_example','ACCOUNT_TOMBSTONE','REDACTED')
        add(e,'audit_example','SECURITY_AUDIT_LOG','PRESENT')
        add(e,'backup_example','BACKUP_ARCHIVE','BLOCKED')
        r=run(e)
        self.assertEqual(r['deletion_status'],'COMPLETE')
        self.assertEqual({s['operation'] for s in json.loads(r['steps_json'])},
                         {'VERIFY_RECORD_PRESENT','VERIFY_RECORD_REDACTED','VERIFY_RESTORE_BLOCKED'})

    def test_post_cutoff_fix_excluded(self):
        e=engine();add(e,'search_example','SEARCH_INDEX_ENTRY','PRESENT')
        add(e,'search_example','SEARCH_INDEX_ENTRY','ABSENT','2026-03-01T00:00:00Z')
        self.assertEqual(run(e)['deletion_status'],'INCOMPLETE')

    def test_replica_not_canceled_by_newer_primary_absence(self):
        e=engine();add(e,'account_example','USER_PROFILE','PRESENT',scope='replica')
        add(e,'account_example','USER_PROFILE','ABSENT','2026-01-20T00:00:00Z',scope='primary')
        self.assertEqual(run(e)['deletion_status'],'INCOMPLETE')

    def test_query_email_is_not_analytics_pii(self):
        self.assertEqual(record_state('ANALYTICS_PROFILE',{'lookup_key':'person@example.test',
                         'email':None,'user_id':None,'phone':None,'email_hash':None}), 'ANONYMIZED')

    def test_no_state_evidence_refuses_completion(self):
        with self.assertRaises(ValueError):run(engine())

    def test_wrapped_log_trace(self):
        d=log_fields('2026-01-01T00:00:00Z [INFO] [account_service] [tr-test] profile_lookup_completed: rows="0"')
        self.assertEqual((d['service'],d['trace_id'],d['event'],d['rows']),
                         ('account_service','tr-test','profile_lookup_completed','0'))

    def test_stringified_null_is_not_pii(self):
        fields=log_fields('event=analytics_profile_read_completed email=null phone=null email_hash=null customer_reference=null')
        self.assertIsNone(fields['email'])
        self.assertEqual(record_state('ANALYTICS_PROFILE',fields),'ANONYMIZED')

    def test_spatial_rows_do_not_merge_customers(self):
        layout={'width':1000,'height':700,'words':[
            {'text':'data_flow_901','x':150,'y':300,'width':95,'height':15},
            {'text':'alice@example.test','x':450,'y':301,'width':130,'height':15},
            {'text':'data_flow_902','x':150,'y':350,'width':95,'height':15},
            {'text':'bob@example.test','x':450,'y':351,'width':130,'height':15}]}
        rows={r:t for r,t,_ in resource_regions(layout)}
        self.assertIn('alice@example.test',rows['data_flow_901'])
        self.assertNotIn('bob@example.test',rows['data_flow_901'])

    def test_stable_subject_does_not_inherit_different_lookup_key(self):
        e=engine()
        def match(data):
            text=' '.join(scalars(data))
            return {uid for uid in ('user_111','user_222') if uid in text}
        e.identities=SimpleNamespace(match=match)
        obs=Observation('support','support_901','SUPPORT_MESSAGE','IDENTIFIABLE',
                        '2026-01-01T00:00:00Z','2026-01-01T00:00:00Z','source',
                        data={'subject_reference':'user_111','lookup_key':'user_222'})
        e.add(obs)
        self.assertEqual(obs.links,{'user_111'})

    def test_other_subject_exposed_in_shared_message_is_discoverable(self):
        e=engine()
        e.identities=SimpleNamespace(match=lambda data:{uid for uid in ('user_111','user_222') if uid in ' '.join(scalars(data))})
        obs=Observation('support','support_902','SUPPORT_MESSAGE','IDENTIFIABLE',
                        '2026-01-01T00:00:00Z','2026-01-01T00:00:00Z','source',
                        data={'subject_reference':'user_111','message_text':'Order shared with user_222'})
        e.add(obs)
        self.assertEqual(obs.links,{'user_111','user_222'})

    def test_phone_in_message_needs_redaction(self):
        self.assertEqual(record_state('SUPPORT_MESSAGE',{'message_text':'Call +44 (7700) 900123 for delivery'}),'IDENTIFIABLE')

    def test_phone_link_normalizes_format(self):
        index=IdentityIndex.__new__(IdentityIndex)
        index.by_value=defaultdict(set);index.values=defaultdict(set);index.by_phone=defaultdict(set)
        index.add('user_example','+44 7700 900123')
        self.assertEqual(index.match({'body':'Call +44 (7700) 900123 for delivery'}),{'user_example'})

    def test_same_scope_later_absence_supersedes_presence(self):
        e=engine();add(e,'account_example','USER_PROFILE','PRESENT',scope='primary')
        add(e,'account_example','USER_PROFILE','ABSENT','2026-01-20T00:00:00Z',scope='primary')
        self.assertEqual(run(e)['deletion_status'],'COMPLETE')

    def test_failed_workflow_discovers_owner_but_readback_decides_state(self):
        for result,state,expected in [('FAILED','ABSENT','COMPLETE'),('SUCCESS','PRESENT','INCOMPLETE')]:
            e=engine();e.activities=[worker('account_901',result)]
            e.add(Observation('account_service','account_901','USER_PROFILE',state,
                              '2026-01-15T00:00:00Z','2026-01-15T00:00:00Z','readback'))
            self.assertEqual(e.audit(request())['deletion_status'],expected)

    def test_null_and_absent_lookup_preserves_identifier_link(self):
        e=engine();e.identities=SimpleNamespace(resolve=lambda email:'subject',
            match=lambda data:{'subject'} if 'alias@example.test' in ' '.join(scalars(data)) else set())
        e.add(Observation('account_service','account_902','USER_PROFILE','ABSENT',
            '2026-01-15T00:00:00Z','2026-01-15T00:00:00Z','readback',
            data={'event':'profile_lookup_completed','lookup_key':'alias@example.test',
                  'email':None,'customer_reference':None,'rows':'0','http_status':'404'}))
        steps=json.loads(e.audit(request())['steps_json'])
        self.assertEqual(steps[0]['operation'],'VERIFY_RECORD_ABSENT')
        self.assertEqual(steps[0]['evidence_id'],'readback')

    def test_incomplete_verifies_every_linked_resource_including_unknown(self):
        e=engine();add(e,'account_903','USER_PROFILE','PRESENT','2026-01-15T00:00:00Z')
        for resource,category in [('audit_record_903','SECURITY_AUDIT_LOG'),('analytics_903','ANALYTICS_PROFILE')]:
            e.add(Observation('other',resource,category,'PRESENT','2026-01-15T00:00:00Z',
                               '2026-03-01T00:00:00Z','future_source',links={'subject'}))
        result=e.audit(request());steps=json.loads(result['steps_json'])
        checks=[s for s in steps if s['phase']=='VERIFICATION']
        self.assertEqual({s['operation'] for s in checks},
                         {'VERIFY_RECORD_ABSENT','VERIFY_RECORD_PRESENT','VERIFY_RECORD_ANONYMIZED'})
        self.assertTrue(all(s['evidence_id']=='' for s in checks))
        self.assertEqual(len([s for s in steps if s['phase']=='FINDING']),1)

    def test_late_discovery_never_supplies_earlier_state_or_citation(self):
        e=engine()
        e.add(Observation('account_service','account_904','USER_PROFILE','PRESENT',
                          '2026-01-10T00:00:00Z','2026-01-10T00:00:00Z','early'))
        e.add(Observation('account_service','account_904','USER_PROFILE','ABSENT',
                          '2026-01-15T00:00:00Z','2026-03-01T00:00:00Z','late',links={'subject'}))
        result=e.audit(request());steps=json.loads(result['steps_json'])
        self.assertEqual(result['deletion_status'],'INCOMPLETE')
        self.assertEqual(steps[0]['evidence_id'],'early')
        self.assertFalse(any(s['evidence_id']=='late' for s in steps))

    def test_pre_request_objects_and_tombstones_are_not_current_episode(self):
        e=engine()
        e.rules['SUPPORT_ATTACHMENT']={'required_action':'DELETE'}
        add(e,'object_901','SUPPORT_ATTACHMENT','PRESENT',system='object_storage')
        add(e,'account_901','USER_PROFILE','ABSENT')
        add(e,'tombstone_901','ACCOUNT_TOMBSTONE','REDACTED')
        add(e,'account_905','USER_PROFILE','ABSENT','2026-01-16T00:00:00Z',system='account_service')
        result=e.audit(request(start='2026-01-15T00:00:00Z'))
        self.assertEqual({s['resource_id'] for s in json.loads(result['steps_json'])},{'account_905'})

    def test_overlapping_workflow_windows_do_not_override_explicit_owner(self):
        e=engine();e.activities=[worker('account_906')]
        e.resource_links[('account_service','account_906')]=[('other_subject','2026-03-01T00:00:00Z','future')]
        self.assertEqual(e.workflow_resources(request(),'subject'),set())

    def test_worker_after_report_is_not_in_window(self):
        e=engine();e.activities=[worker('account_907',time='2026-01-20T00:00:01Z')]
        self.assertEqual(e.workflow_resources(request(),'subject'),set())

    def test_tied_workflow_windows_do_not_assign_resource(self):
        e=engine();e.activities=[worker('account_908')]
        other=request();other['email']='other@example.test'
        e.request_windows=[request(),other]
        e.identities=SimpleNamespace(resolve=lambda email:'other' if email.startswith('other') else 'subject')
        self.assertEqual(e.workflow_resources(request(),'subject'),set())

    def test_historical_lookup_identifier_links_null_record(self):
        e=engine();index=IdentityIndex.__new__(IdentityIndex)
        index.by_value=defaultdict(set);index.values=defaultdict(set);index.by_phone=defaultdict(set)
        index.add('subject','alias@example.test');index.add('subject','former@example.test')
        e.identities=index
        e.add(Observation('account_service','account_909','USER_PROFILE','ABSENT',
            '2026-01-15T00:00:00Z','2026-01-15T00:00:00Z','readback',
            data={'event':'profile_lookup_completed','lookup_key':'former@example.test','profile':None}))
        self.assertEqual(e.audit(request())['deletion_status'],'COMPLETE')


class OwnershipEliminationRegressions(unittest.TestCase):
    def test_unknown_email_in_neighboring_row_vetoes_single_known_subject(self):
        identities=SimpleNamespace(match=lambda text:{'alice'} if 'alice@example.test' in text else set())
        text='export_1 alice@example.test Ready\nexport_2 outsider@example.test Ready'
        context,links,_=media_context(text,[('export_2 outsider@example.test Ready','row:2')],identities)
        self.assertEqual(links,set())
        self.assertNotIn('alice@example.test',context)

    def test_single_customer_header_still_links_resource_without_row_email(self):
        identities=SimpleNamespace(match=lambda text:{'alice'} if 'alice@example.test' in text else set())
        _,links,_=media_context('account_1\nEmail alice@example.test',[('account_1','header')],identities)
        self.assertEqual(links,{'alice'})

    def test_extended_window_assigns_late_event_only_if_unique(self):
        from audit.ownership import build,resolved_for
        e,a,b=self.fixture(b_start='2026-01-25T00:00:00Z')
        e.request_windows=[a]
        e.activities=[worker('account_824',time='2026-01-21T00:00:00Z')]
        self.assertEqual(resolved_for(build(e,[a]),a,e.identities),set())
        self.assertEqual(resolved_for(build(e,[a],extended=True),a,e.identities),{('account_service','account_824')})
        e.activities.append(worker('account_825',time='2026-01-22T00:00:00Z'))
        self.assertEqual(resolved_for(build(e,[a],extended=True),a,e.identities),set())

    def test_trace_records_grounding_source_and_each_elimination(self):
        from audit.ownership import build
        e,a,b=self.fixture()
        e.activities=[worker('account_826'),worker('account_827')]
        e.resource_links[('account_service','account_826')]=[('alice','2026-01-10T00:00:00Z','lookup_fixture')]
        trace=build(e,[a,b])['trace']
        self.assertTrue(any('lookup_fixture' in row.get('evidence_ids',[]) for row in trace))
        self.assertTrue(any(row['action']=='assign_unique' for row in trace))

    def fixture(self, a_start='2026-01-01T00:00:00Z', b_start='2026-01-01T00:00:00Z'):
        e=engine();e.enable_ownership_elimination=True
        e.identities=SimpleNamespace(resolve=lambda email:email.split('@')[0],match=lambda data:set())
        a=request(start=a_start);a.update(email='alice@example.test',case_id='first')
        b=request(start=b_start);b.update(email='bob@example.test',case_id='second')
        e.request_windows=[a,b]
        return e,a,b

    def test_unique_candidate_after_iterative_elimination_is_assigned(self):
        e,a,b=self.fixture(b_start='2026-01-10T00:00:00Z')
        e.activities=[worker('account_811',time='2026-01-04T00:00:00Z'),
                      worker('account_812',time='2026-01-12T00:00:00Z')]
        # Alice has {811,812}; Bob has {812}. Bob's forced assignment leaves
        # only 811 for Alice on the next iteration.
        self.assertEqual(e.workflow_resources(a,'alice'),{('account_service','account_811')})
        self.assertEqual(e.workflow_resources(b,'bob'),{('account_service','account_812')})

    def test_two_candidates_left_remain_unassigned_and_recorded(self):
        e,a,b=self.fixture()
        e.activities=[worker('account_813'),worker('account_814')]
        self.assertEqual(e.workflow_resources(a,'alice'),set())
        self.assertEqual(e.workflow_resources(b,'bob'),set())
        issues=[d for d in e.diagnostics if d['issue']=='Unresolved workflow ownership']
        self.assertEqual(len(issues),2)
        self.assertTrue(all(len(d['candidates'])==2 for d in issues))

    def test_grounded_owner_removes_candidate_from_another_request(self):
        e,a,b=self.fixture()
        e.activities=[worker('account_815'),worker('account_816')]
        e.resource_links[('account_service','account_815')]=[('alice','2026-03-01T00:00:00Z','direct_lookup')]
        self.assertEqual(e.workflow_resources(a,'alice'),{('account_service','account_815')})
        self.assertEqual(e.workflow_resources(b,'bob'),{('account_service','account_816')})

    def test_contested_singleton_is_not_awarded_by_iteration_order(self):
        e,a,b=self.fixture();e.activities=[worker('account_817')]
        self.assertEqual(e.workflow_resources(a,'alice'),set())
        self.assertEqual(e.workflow_resources(b,'bob'),set())

    def test_candidate_resolution_independent_of_input_order(self):
        from audit.ownership import build
        e,a,b=self.fixture(b_start='2026-01-10T00:00:00Z')
        e.activities=[worker('account_818',time='2026-01-04T00:00:00Z'),
                      worker('account_819',time='2026-01-12T00:00:00Z')]
        first=build(e,[a,b])
        e.activities.reverse()
        second=build(e,[b,a])
        self.assertEqual(first['assigned'],second['assigned'])
        self.assertEqual(first['unresolved'],second['unresolved'])

    def test_conflicting_grounded_primary_accounts_do_not_pick_one(self):
        from audit.ownership import eliminate
        slot=(('alice','start','end'),'primary_account')
        accounts={('account_service','account_822'),('account_service','account_823')}
        assigned,unresolved=eliminate({}, {slot:accounts})
        self.assertNotIn(slot,assigned)
        self.assertEqual(unresolved[slot],accounts)

    def test_eliminated_ownership_never_uses_late_state(self):
        e,a,b=self.fixture(b_start='2026-01-10T00:00:00Z')
        e.activities=[worker('account_820',time='2026-01-04T00:00:00Z'),
                      worker('account_821',time='2026-01-12T00:00:00Z')]
        e.add(Observation('account_service','account_821','USER_PROFILE','PRESENT',
                          '2026-01-15T00:00:00Z','2026-01-15T00:00:00Z','eligible'))
        e.add(Observation('account_service','account_821','USER_PROFILE','ABSENT',
                          '2026-01-16T00:00:00Z','2026-03-01T00:00:00Z','late'))
        result=e.audit(b)
        self.assertEqual(result['deletion_status'],'INCOMPLETE')
        self.assertEqual(json.loads(result['steps_json'])[0]['evidence_id'],'eligible')


if __name__=='__main__':unittest.main()
