from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from pl_dna.season_feed import normalize_player, normalize_reference, match_info, fetch_json, fetch_player_stats
from pl_dna.season_comparison import compare_season_player
from pl_dna.current_dashboard import load_current, fingerprint, auto_story_due, suggested_role, wheel
from pl_dna.legend_blend import generate_blend_story, fit_blend

ROOT = Path(__file__).resolve().parents[1]


def raw_stats(snapshot):
    """Explicitly simulated transport fixture; never a product match record."""
    from pl_dna.season_feed import FIELDS
    values = {FIELDS[k][1]:v for k,v in snapshot['counts'].items() if v is not None}
    values.update(minutes=snapshot['minutes'],totalGoals=snapshot['goals'],goalAssists=snapshot['assists'])
    fields = [{'name':k,'value':v} for k,v in values.items()]
    return {'splits': {'categories': [{'stats':fields}]}}


class CurrentSeasonTests(unittest.TestCase):
    def setUp(self):
        self.research_env=patch.dict('os.environ',{'PL_DNA_ENABLE_RESEARCH':'1'})
        self.research_env.start();self.addCleanup(self.research_env.stop)

    @classmethod
    def setUpClass(cls):
        cls.study = load_current()

    def payload(self, entry=None):
        e = deepcopy(entry or next(iter(self.study['targets'].values())))
        return compare_season_player(e['player'],e['snapshot'],e['fixture'],self.study['references'],e['role'])

    def test_all_examples_are_real_current_season_snapshots_with_provenance(self):
        self.assertEqual(len(self.study['targets']), 8)
        self.assertEqual({e['role'] for e in self.study['targets'].values()}, {'GK','CB','FB','CDM','CM','CAM','WING','ST'})
        self.assertEqual(len({e['player']['team_id'] for e in self.study['targets'].values()}),8)
        names = [t['player']['name'] for t in self.study['targets'].values()]
        for name in ['Enzo Fernández','Bruno Fernandes','Virgil van Dijk','Zion Suzuki','Antonee Robinson','Moisés Caicedo','Diego Gómez','Igor Thiago']:
            self.assertIn(name,names)
        for e in self.study['targets'].values():
            self.assertTrue(e['fixture']['date'].startswith('2026-10-'))
            self.assertEqual(e['fixture']['state'],'post')
            self.assertEqual(len(e['snapshot']['source']['sha256']),64)
            p = self.payload(e)
            if p['availability']:
                self.assertEqual(e['role'],'CDM')
                self.assertTrue(p['interpretation_available'])
                self.assertNotIn('fit',p)
                continue
            self.assertEqual(sum(p['fit']['percentages'].values()),100)
            self.assertTrue(all(v>=0 for v in p['fit']['weights'].values()))
            self.assertNotIn('shots',p['metric_keys'])  # Explicit source disagreement is preserved.
            for k in p['metric_keys']:
                self.assertAlmostEqual(p['target_rates'][k],90*e['snapshot']['counts'][k]/e['snapshot']['minutes'])

    def test_missing_is_not_zero_and_disputed_metrics_are_not_used(self):
        entry = next(e for e in self.study['targets'].values() if e['role']=='CM')
        raw = raw_stats(entry['snapshot'])
        values = raw['splits']['categories'][0]['stats']
        values[:] = [x for x in values if x['name'] != 'interceptions']
        values += [{'name':'accuratePasses','value':10}, {'name':'inaccuratePasses','value':1}]
        s = normalize_player(raw,{'url':'test','checked_at':'test'})
        self.assertIsNone(s['counts']['interceptions'])
        self.assertIn('passes',s['excluded_metrics'])
        e = deepcopy(entry);e['snapshot']=s
        p = self.payload(e)
        self.assertNotIn('interceptions',p.get('metric_keys',[]))
        self.assertNotIn('passes',p.get('metric_keys',[]))
        s['minutes'] = None
        self.assertTrue(self.payload(e)['availability'])

    def test_reference_requires_real_minutes_and_no_proxy_denominator(self):
        with self.assertRaises(ValueError):
            normalize_reference({'stats':{'appearances':38}}, {}, 2010, 'CM','test')
        p = self.payload()
        p2 = deepcopy(p)
        p2['target']['source']['checked_at']='tomorrow'
        p2['fixture']['clock']='99'
        self.assertEqual(fingerprint(p),fingerprint(p2))
        p2['target']['counts']['passes']+=1
        self.assertNotEqual(fingerprint(p),fingerprint(p2))

    def test_automatic_ai_is_opt_in_throttled_changed_live_and_fresh_only(self):
        self.assertTrue(auto_story_due(True,'in',True,1300,1000))
        for args in [(False,'in',True,1300,1000,False),(True,'post',True,1300,1000,False),
                     (True,'pre',True,1300,1000,False),(True,'in',False,1300,1000,False),
                     (True,'in',True,1299,1000,False),(True,'in',True,1300,1000,True)]:
            self.assertFalse(auto_story_due(*args))

    def test_provider_story_uses_seasons_and_never_archived_match_sample_claims(self):
        p = self.payload()
        p['fit_status']='candidate_mix'  # Exercise this wording branch independently of sample fit.
        provider = Mock(side_effect=lambda p:{'angle':'closest_sample','lead':p['evidence'][0]['id'],'support':None})
        r = generate_blend_story(p,provider)
        self.assertEqual(r['status'],'verified')
        self.assertIn('reference seasons',r['text'])
        self.assertNotIn('three match samples',r['text'])
        self.assertIn('per 90',r['text'])
        self.assertNotIn('per 100 on-ball',r['text'])

    def test_weak_fit_never_forces_percentages_or_an_ability_grade(self):
        e=deepcopy(next(iter(self.study['targets'].values())))
        e['snapshot']['counts']={k:(None if v is None else v*100+100) for k,v in e['snapshot']['counts'].items()}
        p=self.payload(e)
        self.assertEqual(p['fit_status'],'no_clear_match')
        r=generate_blend_story(p,lambda q:{'angle':'contrast','lead':q['evidence'][0]['id'],'support':None})
        self.assertEqual(r['status'],'verified')
        self.assertIn('No clear match',r['text'])
        self.assertIn('not an overall performance grade',r['text'])
        self.assertNotIn('%',r['text'])
        self.assertNotIn('#b69aff',wheel(p))
        self.assertIn('No composite reference shown',wheel(p))

    def test_weak_match_ui_keeps_player_wheel_without_legend_percent_cards(self):
        from streamlit.testing.v1 import AppTest
        study=deepcopy(self.study)
        e=next(iter(study['targets'].values()))
        e['snapshot']['counts']={k:(None if v is None else v*100+100) for k,v in e['snapshot']['counts'].items()}
        with patch('pl_dna.current_dashboard.load_current',return_value=study), \
             patch('pl_dna.current_dashboard.wheel', wraps=wheel) as player_wheel, \
             patch('pl_dna.microsoft_provider.create_provider_from_env') as provider:
            at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
            self.assertEqual(list(at.exception),[])
            self.assertTrue(any('No clear match' in x.value for x in at.info))
            self.assertFalse(any(m.value.endswith('%') for m in at.metric))
            player_wheel.assert_called_once()
            self.assertEqual(player_wheel.call_args.args[0]['fit_status'],'no_clear_match')
            provider.assert_not_called()

    def test_execution_can_explain_a_weak_match_without_resemblance(self):
        p=self.payload()
        p['fit_status']='no_clear_match'
        fact=next(e for e in p['evidence'] if e.get('kind')=='execution')
        result=generate_blend_story(p,lambda q:{'angle':'contrast','lead':fact['id'],'support':None})
        self.assertEqual(result['status'],'verified')
        self.assertIn(fact['sentence'],result['text'])
        self.assertNotIn('reference seasons',result['text'])
        p2=deepcopy(p)
        next(iter(p2['target']['execution'].values()))['successful']+=1
        self.assertNotEqual(fingerprint(p),fingerprint(p2))

    def test_execution_does_not_change_style_fit_and_short_samples_block_ai(self):
        e=deepcopy(next(iter(self.study['targets'].values())))
        before=self.payload(e)
        e['snapshot']['execution']={'Pass completion':{'successful':1,'attempted':50,'percentage':2.0}}
        after=self.payload(e)
        self.assertEqual(before['fit'],after['fit'])
        self.assertEqual(before['fit_status'],after['fit_status'])
        e['snapshot']['minutes']=10
        insufficient=self.payload(e)
        provider=Mock()
        self.assertEqual(generate_blend_story(insufficient,provider)['status'],'insufficient')
        provider.assert_not_called()

    def test_role_suggestions_and_missing_legend_coverage(self):
        for position,role in [('Goalkeeper','GK'),('Left Back','FB'),('Center Defender','CB'),
                              ('Forward Left','WING'),('Forward','ST'),('Defensive Midfielder','CDM'),
                              ('Attacking Midfielder','CAM'),('Center Midfielder','CM')]:
            self.assertEqual(suggested_role({'id':'x','source_position':position},{}),role)
        self.assertIsNone(suggested_role({'id':'x','source_position':'Unknown'},{}))
        names={r['player'] for r in self.study['unavailable_references']}
        self.assertTrue({'Alan Shearer','Thierry Henry','Peter Schmeichel'}.issubset(names))
        for r in self.study['unavailable_references']:
            self.assertNotIn('counts',r)

    def test_two_and_four_reference_simplex_recovery(self):
        for n in (2,4):
            keys=list('abcd')[:n]
            refs={str(i):{'rates':{k:float(i==j) for j,k in enumerate(keys)}} for i in range(n)}
            result=fit_blend({'rates':{k:1/n for k in keys}},refs,keys)
            self.assertAlmostEqual(result['rmse'],0)
            for value in result['weights'].values():self.assertAlmostEqual(value,1/n)

    def test_network_boundary_rejects_arbitrary_urls_and_ids_without_calling(self):
        transport = Mock()
        with self.assertRaises(ValueError):
            fetch_json('https://evil.example/data',transport)
        with self.assertRaises(ValueError):
            fetch_player_stats('123','456','../789',transport)
        transport.assert_not_called()

    def test_all_recorded_ui_selections_render_offline_and_do_not_call_models(self):
        from streamlit.testing.v1 import AppTest
        with patch('pl_dna.microsoft_provider.create_provider_from_env',new=Mock()) as provider, \
             patch('pl_dna.current_dashboard.fetch_summary',side_effect=AssertionError('unexpected network')):
            at = AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
            for key in self.study['targets']:
                at.selectbox(key='current_target').select(key).run()
                self.assertEqual(list(at.exception),[])
                self.assertEqual(len(at.slider),0)  # No fake/interpolated historical clock.
            self.assertFalse(any(r.key=='audience' for r in at.radio))
            provider.assert_not_called()

    def test_live_refresh_replaces_snapshot_and_stale_feed_is_labelled(self):
        from streamlit.testing.v1 import AppTest
        e = deepcopy(next(iter(self.study['targets'].values())))
        mid,pid,tid=e['fixture']['id'],e['player']['id'],e['player']['team_id']
        # Simulated live response assembled from a sourced completed-match record.
        summary={'header':{'id':mid,'season':{'year':2026},'competitions':[{
            'date':e['fixture']['date'],'status':{'type':{'state':'in','description':'In Progress'},'displayClock':"90'",'period':2},
            'competitors':[{'homeAway':'home','team':{'displayName':e['fixture']['home']},'score':'2'},
                           {'homeAway':'away','team':{'displayName':e['fixture']['away']},'score':'1'}]}]},
            'rosters':[{'team':{'id':tid,'displayName':e['player']['team']},'roster':[{
                'starter':True,'athlete':{'id':pid,'displayName':e['player']['name']},
                'position':{'displayName':'Center Midfielder'}}]}]}
        board={'events':[{'id':mid,'name':'Test live fixture','status':{'type':{'description':'In Progress'}}}]}
        source=dict(e['snapshot']['source'],http_age_seconds='0')
        raw=raw_stats(e['snapshot'])
        getter=Mock(return_value=(raw,source))
        with patch('pl_dna.current_dashboard.cached_scoreboard',return_value=(board,source)), \
             patch('pl_dna.current_dashboard.cached_summary',return_value=(summary,source)), \
             patch('pl_dna.current_dashboard.cached_player',getter), \
             patch('pl_dna.microsoft_provider.create_provider_from_env') as provider, \
             patch('pl_dna.current_dashboard.now_seconds',return_value=1000) as now:
            inference=Mock(side_effect=lambda p:{'angle':'closest_sample','lead':p['evidence'][0]['id'],'support':None})
            provider.return_value=inference
            at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
            at.radio(key='current_match_mode').set_value('Follow a live match').run()
            getter.assert_not_called()
            at.toggle(key='connect_live_feed').set_value(True).run()
            self.assertEqual(list(at.exception),[])
            old = at.session_state['last_player_snapshot_'+mid+':'+pid]['counts']['passes']
            at.run()
            self.assertEqual(at.session_state['last_player_snapshot_'+mid+':'+pid]['counts']['passes'],old)
            changed=deepcopy(raw)
            next(f for f in changed['splits']['categories'][0]['stats'] if f['name']=='totalPasses')['value']+=1
            getter.return_value=(changed,source)
            at.run()
            self.assertEqual(at.session_state['last_player_snapshot_'+mid+':'+pid]['counts']['passes'],old+1)
            provider.assert_not_called()
            at.checkbox(key='season_auto_ai').check().run()
            self.assertEqual(inference.call_count,1)
            next(f for f in changed['splits']['categories'][0]['stats'] if f['name']=='totalPasses')['value']+=1
            now.return_value=1100
            at.run()
            self.assertEqual(inference.call_count,1)
            now.return_value=1300
            at.run()
            self.assertEqual(inference.call_count,2)
            getter.side_effect=OSError('source unavailable')
            now.return_value=1600
            at.run()
            self.assertEqual(list(at.exception),[])
            self.assertTrue(any('Stale or unavailable' in w.value for w in at.warning))
            self.assertEqual(inference.call_count,2)
            getter.side_effect=None
            summary['header']['competitions'][0]['status']['type']={'state':'post','description':'Full Time'}
            now.return_value=1900
            at.run()
            self.assertEqual(inference.call_count,2)
            self.assertTrue(any('Full time' in x.value for x in at.success))


if __name__=='__main__':unittest.main()
