import json,time,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from copy import deepcopy
from pl_dna.synthetic_replay import advance_clock,synthetic_brief_payload,brief_fingerprint,auto_brief_due
from pl_dna.roles import generate_role_events,PLAYERS
from pl_dna.analyst_brief import generate_analyst_brief

ROOT=Path(__file__).resolve().parents[1]
def simulated_synthetic_brief(p):
    ids=[];seen=set()
    for e in p['evidence']:
        if e['metric'] not in seen:ids.append(e['id']);seen.add(e['metric'])
        if len(ids)==2:break
    narrative=('This synthetic demonstration shows the selected player contributing through several recorded actions. '
        'The combination gives a useful picture of involvement, while the individual measurements remain available for inspection. '
        'These observations describe activity within the selected window and cannot establish overall quality, tactical intent or a resemblance to a historical player.')
    if p.get('focus')=='Broadcast talking point':
        narrative='The selected player gets into the box and moves the ball forward in this synthetic demo. Those actions show involvement, without establishing finishing quality.'
    if p['language']=='Spanish':narrative='Esta demostración sintética combina varias acciones registradas para describir la participación del jugador. Las mediciones permiten seguir su contribución, pero no establecen por sí solas la calidad global, las intenciones tácticas ni una semejanza histórica.'
    return {'headline':'Recorded contributions in a synthetic performance','narrative':narrative,'evidence_ids':ids}

class ReplayTests(unittest.TestCase):
 def test_opt_in_auto_recaps_throttle_and_do_not_retry_failed_context(self):
  from streamlit.testing.v1 import AppTest
  with patch.dict('os.environ',{'PL_DNA_ENABLE_RESEARCH':'0'}), \
       patch('pl_dna.microsoft_provider.create_provider_from_env',return_value=Mock(side_effect=simulated_synthetic_brief)) as factory:
   at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
   at.radio(key='insight_source').set_value('Microsoft AI').run();factory.assert_not_called()
   at.checkbox(key='synthetic_auto_ai').check().run()
   factory.assert_not_called()  # Paused mid-match; opting in is not itself a generation.
   at.button(key='replay_toggle').click().run()
   self.assertEqual(factory.return_value.call_count,1)
   at.session_state['replay_last_tick']=time.monotonic()-3
   at.run();self.assertEqual(factory.return_value.call_count,1)
   at.button(key='replay_toggle').click().run()
   at.slider(key='minute').set_value(90).run()
   self.assertEqual(factory.return_value.call_count,1)
   factory.return_value.side_effect=OSError('private-error-details')
   at.session_state['synthetic_last_ai_attempt']=time.monotonic()-31
   at.run();self.assertEqual(factory.return_value.call_count,2)
   self.assertEqual(list(at.exception),[])
   at.session_state['synthetic_last_ai_attempt']=time.monotonic()-31
   at.run();self.assertEqual(factory.return_value.call_count,2)
   self.assertFalse(any('private-error-details' in i.value for i in at.info))

 def test_clock_pause_catchup_and_fulltime_boundaries(self):
  state={'minute':43,'replay_playing':True,'replay_last_tick':10,'replay_step':3}
  advance_clock(state,11.99);self.assertEqual(state['minute'],43)
  advance_clock(state,14);self.assertEqual(state['minute'],49)
  state['replay_playing']=False;advance_clock(state,100);self.assertEqual(state['minute'],49)
  state['replay_playing']=True;advance_clock(state,100);self.assertEqual(state['minute'],90)
  self.assertFalse(state['replay_playing'])

 def test_all_positions_reconstruct_counts_without_future_evidence(self):
  data=generate_role_events(42)
  for player in PLAYERS:
   for end in (15,43,90):
    p=synthetic_brief_payload(data,player,0,end)
    observed=set(data.loc[data.minute.le(end),'event_id'])
    for e in p['evidence']:
     self.assertTrue(set(e['event_ids'])<=observed)
     self.assertTrue(set(e['supporting_event_ids'])<=observed)
     if e['kind']=='recorded':self.assertEqual(e['count'],len(e['event_ids']))
    self.assertNotIn('experimental_reference_scores',p)
    self.assertEqual(p['phase'],'full_time_recap' if end==90 else 'match_in_progress')

 def test_personalization_changes_ai_context_and_insufficient_data_blocks_calls(self):
  data=generate_role_events(42);player='Alex Morganfield'
  p=synthetic_brief_payload(data,player,0,90)
  self.assertTrue(any(e['kind']=='window_change' for e in p['evidence']))
  q=synthetic_brief_payload(data,player,0,90,language='Spanish',focus='Broadcast talking point')
  self.assertNotEqual(brief_fingerprint(p),brief_fingerprint(q))
  self.assertEqual(generate_analyst_brief(q,simulated_synthetic_brief)['status'],'evidence_checked')
  short=synthetic_brief_payload(data,player,0,1);model=Mock()
  self.assertEqual(generate_analyst_brief(short,model)['status'],'insufficient');model.assert_not_called()

 def test_synthetic_attribution_and_legend_claim_checks(self):
  p=synthetic_brief_payload(generate_role_events(42),'Alex Morganfield',0,90)
  reply=simulated_synthetic_brief(p);reply['narrative']=reply['narrative'].replace('synthetic','recorded')
  self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'evidence_checked')
  reply=simulated_synthetic_brief(p);reply['headline']='Rooney resemblance in the synthetic performance'
  self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'fallback')

 def test_illustrative_candidates_reconstruct_existing_scores_and_reject_unqualified_claim(self):
  from pl_dna.roles import score_role_profiles
  data=generate_role_events(42)
  for player in PLAYERS:
   p=synthetic_brief_payload(data,player,0,90)
   comparison=p['illustrative_comparison']
   self.assertEqual(comparison['status'],'illustrative_candidates')
   scores=score_role_profiles(data,player,0,90)
   self.assertEqual(comparison['candidates'][0]['profile'],scores.index[0])
   for c in comparison['candidates']:
    self.assertEqual(c['score'],round(float(scores.loc[c['profile'],'experimental_resemblance_score']),1))
    self.assertTrue(all(a['evidence_id'] in {e['id'] for e in p['evidence']} for a in c['axes']))
  p=synthetic_brief_payload(data,'Alex Morganfield',0,90)
  reply=simulated_synthetic_brief(p)
  reply['narrative']='Morganfield shows a Lampard-inspired pattern in this synthetic demo, getting into the box and taking shots. This illustrative profile comparison describes recorded involvement against an invented reference, rather than establishing historical similarity or overall player quality.'
  self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'evidence_checked')
  reply['narrative']=reply['narrative'].replace('illustrative','recognizable').replace('invented','familiar')
  self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'evidence_checked')
  reply['narrative']=reply['narrative'].replace('Lampard','Rooney')
  self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'fallback')

 def test_insufficient_and_distant_profiles_never_force_legend_candidates(self):
  from pl_dna.synthetic_replay import illustrative_profile_context
  import pandas as pd
  data=generate_role_events(42)
  self.assertEqual(illustrative_profile_context(data,'Alex Morganfield',0,1)['candidates'],[])
  distant=pd.DataFrame({'weighted_distance':[3.0], 'experimental_resemblance_score':[25.0]},index=['Box-to-box attacker'])
  with patch('pl_dna.synthetic_replay.score_role_profiles',return_value=distant):
   c=illustrative_profile_context(data,'Alex Morganfield',0,90)
  self.assertEqual(c['status'],'no_clear_profile');self.assertEqual(c['candidates'],[])
  p=synthetic_brief_payload(data,'Alex Morganfield',0,43)
  earlier=data[data.minute.le(43)].copy()
  self.assertEqual(p['illustrative_comparison'],illustrative_profile_context(earlier,'Alex Morganfield',0,43))

 def test_calculated_legend_explanation_survives_ai_failure(self):
  from pl_dna.analyst_brief import calculated_profile_story
  data=generate_role_events(42)
  p=synthetic_brief_payload(data,'Noah Bennett',0,67)
  story=calculated_profile_story(p)
  self.assertIn('Terry-inspired',story);self.assertIn('Vidic-inspired',story)
  self.assertIn('invented profiles',story);self.assertIn('not validated historical',story)
  self.assertNotIn('%',story)
  result=generate_analyst_brief(p,Mock(side_effect=ValueError('offline')))
  self.assertEqual(result['status'],'fallback')
  self.assertEqual(calculated_profile_story(p),story)
  p['language']='Spanish';self.assertIn('perfiles inventados',calculated_profile_story(p))

 def test_optional_auto_cost_guard(self):
  state={'synthetic_last_ai_key':'old','synthetic_last_ai_attempt':100}
  self.assertTrue(auto_brief_due(True,True,43,'new',state,130))
  self.assertTrue(auto_brief_due(True,False,90,'new',state,130))
  for args in [(False,True,43,'new',state,130),(True,False,43,'new',state,130),
               (True,True,43,'old',state,130),(True,True,43,'new',state,129)]:
   self.assertFalse(auto_brief_due(*args))

 def test_default_submission_ui_replay_microsoft_and_fulltime_recap(self):
  from streamlit.testing.v1 import AppTest
  with patch.dict('os.environ',{'PL_DNA_ENABLE_RESEARCH':'0'}), \
       patch('pl_dna.microsoft_provider.create_provider_from_env',return_value=Mock(side_effect=simulated_synthetic_brief)) as factory, \
       patch('pl_dna.current_dashboard.fetch_scoreboard',side_effect=AssertionError('Submission must not read real feeds')):
   at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
   self.assertEqual(list(at.exception),[])
   self.assertEqual(at.radio(key='data_source').options,['Eight-position synthetic demo'])
   at.radio(key='insight_source').set_value('Microsoft AI').run();factory.assert_not_called()
   at.button(key='synthetic_generate_brief').click().run()
   self.assertEqual(list(at.exception),[]);factory.return_value.assert_called_once()
   p=factory.return_value.call_args.args[0]
   self.assertEqual(p['data_kind'],'synthetic')
   at.button(key='replay_toggle').click().run()
   at.session_state['replay_last_tick']=time.monotonic()-3
   at.run();self.assertGreater(at.slider(key='minute').value,43)
   self.assertTrue(any('As of synthetic minute 43' in c.value for c in at.caption))
   self.assertEqual(factory.return_value.call_count,1)
   at.button(key='replay_toggle').click().run()
   at.slider(key='minute').set_value(90).run()
   self.assertEqual(at.button(key='synthetic_generate_brief').label,'Generate Microsoft recap')
   at.button(key='synthetic_generate_brief').click().run()
   self.assertEqual(factory.return_value.call_count,2)
   self.assertEqual(factory.return_value.call_args.args[0]['phase'],'full_time_recap')
   self.assertTrue(any('full-time recap' in c.value for c in at.caption))
   at.selectbox(key='insight_language').select('Spanish').run()
   self.assertFalse(any('Synthetic full-time recap · Microsoft' in c.value for c in at.caption))
   self.assertEqual(factory.return_value.call_count,2)
