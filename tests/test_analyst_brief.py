from copy import deepcopy
import io
import json
import unittest
from unittest.mock import Mock, patch
from pl_dna.analyst_brief import generate_analyst_brief
from pl_dna.current_dashboard import load_current
from pl_dna.season_comparison import compare_season_player
from pl_dna.microsoft_provider import create_provider_from_env


def simulated_brief(p):
    """Test prose only; not a product match interpretation."""
    ids=[];metrics=set()
    for e in p['evidence']:
        if e['metric'] not in metrics:
            ids.append(e['id']);metrics.add(e['metric'])
        if len(ids)==2:break
    return {'headline':'Shot stopping and distribution in focus',
        'narrative':'The recorded activity points to a contrast between shot stopping and distribution. That gives the performance a clearer shape than a single blend label, although these limited match counts cannot establish overall quality or explain the tactical circumstances.',
        'evidence_ids':ids}


class AnalystTests(unittest.TestCase):
    def setUp(self):
        self.research_env=patch.dict('os.environ',{'PL_DNA_ENABLE_RESEARCH':'1'})
        self.research_env.start();self.addCleanup(self.research_env.stop)

    def payload(self):
        study=load_current();e=next(iter(study['targets'].values()))
        return compare_season_player(e['player'],e['snapshot'],e['fixture'],study['references'],e['role'])

    def test_ai_writes_interpretation_and_exact_facts_are_attached_locally(self):
        p=self.payload();provider=Mock(side_effect=simulated_brief)
        result=generate_analyst_brief(p,provider)
        self.assertEqual(result['status'],'evidence_checked')
        self.assertEqual(provider.call_args.args[0]['task'],'performance_interpretation')
        self.assertEqual(result['text'],simulated_brief(p)['narrative'])
        self.assertEqual(result['facts'],[next(e['sentence'] for e in p['evidence'] if e['id']==i) for i in result['evidence_ids']])

    def test_invalid_numbers_citations_grades_and_forced_legend_names_are_rejected(self):
        p=self.payload();p['fit_status']='no_clear_match'
        for field,value in [('narrative','He completed 99 passes and dominated this match. '+simulated_brief(p)['narrative']),
                            ('evidence_ids',['invented','invented2']),
                            ('headline','The best player on the pitch'),
                            ('headline','A Cech style performance'),
                            ('narrative','<script>alert</script> '+simulated_brief(p)['narrative'])]:
            reply=simulated_brief(p);reply[field]=value
            self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'fallback')
        reply=simulated_brief(p);reply['evidence_ids']*=2
        self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'fallback')

    def test_complete_briefs_are_not_rejected_or_cut_for_editorial_length(self):
        for phase in ('match_in_progress','full_time_recap'):
            for focus in ('Fan explanation','Broadcast talking point'):
                for words in (19,43,54,58,69,111,250):
                    p=self.payload();p.update(focus=focus,phase=phase)
                    reply=simulated_brief(p)
                    reply['headline']='A detailed football headline that is allowed to exceed the old editorial headline word count limit'
                    reply['narrative']=' '.join(['football']*words)+'.'
                    provider=Mock(return_value=reply)
                    result=generate_analyst_brief(p,provider)
                    self.assertEqual(result['status'],'evidence_checked')
                    self.assertEqual(result['text'],reply['narrative'])
                    self.assertFalse(result['shortened'])
                    provider.assert_called_once()

    def test_empty_text_is_still_rejected(self):
        p=self.payload()
        for field in ('headline','narrative'):
            reply=simulated_brief(p);reply[field]='   '
            self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'fallback')

    def test_synthetic_trend_requires_cited_change_not_just_available_change(self):
        from pl_dna.synthetic_replay import synthetic_brief_payload
        from pl_dna.roles import generate_role_events
        p=synthetic_brief_payload(generate_role_events(42),'Alex Morganfield',0,90)
        reply=simulated_brief(p)
        reply['narrative']='This synthetic demo shows a recent shift in passing. '+reply['narrative']
        reply['evidence_ids']=[e['id'] for e in p['evidence'] if e['kind']=='recorded'][:2]
        self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'fallback')
        change=next(e for e in p['evidence'] if e['kind']=='window_change')
        other=next(e for e in p['evidence'] if e['metric']!=change['metric'])
        reply['evidence_ids']=[change['id'],other['id']]
        self.assertEqual(generate_analyst_brief(p,lambda _:reply)['status'],'evidence_checked')

    def test_unsupported_trend_continuation_is_removed_without_retry_or_leaking_copy(self):
        from pl_dna.synthetic_replay import synthetic_brief_payload
        from pl_dna.roles import generate_role_events
        p=synthetic_brief_payload(generate_role_events(42),'Noah Bennett',0,67)
        reply=simulated_brief(p)
        reply['headline']='A recent shift in defending'
        opening='In this synthetic demonstration, Bennett contributes through tackles and interceptions.'
        reply['narrative']=opening+' His aerial duels increased recently. This points to a new tactical role.'
        provider=Mock(return_value=reply)
        result=generate_analyst_brief(p,provider)
        self.assertEqual(result['status'],'evidence_checked')
        self.assertEqual(result['text'],opening)
        self.assertNotIn('increased',str(result));self.assertNotIn('tactical',str(result))
        self.assertNotIn('recent',result['headline'])
        self.assertIn('Evidence edit',result['style_note']);provider.assert_called_once()

    def test_supporter_story_without_repeated_disclaimers_is_accepted(self):
        from pl_dna.synthetic_replay import synthetic_brief_payload
        from pl_dna.roles import generate_role_events
        p=synthetic_brief_payload(generate_role_events(42),'Alex Morganfield',0,90)
        reply=simulated_brief(p)
        reply['headline']='Morganfield is not shy about having a go'
        reply['narrative']="I like the combination here: Morganfield gets into the box and has a go. There is a Lampard-inspired feel to that part of his game, with passing that moves the ball forward adding another talking point."
        result=generate_analyst_brief(p,lambda _:reply)
        self.assertEqual(result['status'],'evidence_checked')
        self.assertEqual(result['text'],reply['narrative'])
        self.assertEqual(result['data_kind'],'synthetic')

    def test_synthetic_adapter_uses_selected_voice_without_legacy_instruction_stack(self):
        from pl_dna.synthetic_replay import synthetic_brief_payload
        from pl_dna.roles import generate_role_events
        p=synthetic_brief_payload(generate_role_events(42),'Alex Morganfield',0,90)
        p['instructions']=['LEGACY_INSTRUCTION_SHOULD_NOT_REACH_MODEL']
        candidate=simulated_brief(p)
        env={'PL_DNA_ENABLE_AZURE':'1','AZURE_OPENAI_BASE_URL':'https://demo.openai.azure.com/openai/v1/',
             'AZURE_OPENAI_API_KEY':'test-placeholder','AZURE_OPENAI_DEPLOYMENT':'test'}
        prompts=[]
        for focus in ('Fan explanation','Broadcast talking point'):
            p['focus']=focus
            transport=Mock(return_value=io.BytesIO(json.dumps({'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(candidate)}]}]}).encode()))
            create_provider_from_env(env,transport)(p)
            prompt=json.loads(transport.call_args.args[0].data)['input']
            self.assertNotIn('LEGACY_INSTRUCTION_SHOULD_NOT_REACH_MODEL',prompt)
            prompts.append(prompt.split('DATA:')[0])
        self.assertNotEqual(prompts[0],prompts[1])

    def test_unknown_evidence_rejection_does_not_expose_ids(self):
        p=self.payload();reply=simulated_brief(p)
        reply['evidence_ids']=['secret-provider-value','unknown']
        result=generate_analyst_brief(p,lambda _:reply)
        self.assertNotIn('secret-provider-value',result['reason'])
        self.assertIn('unavailable evidence',result['reason'])

    def test_provider_errors_never_echo_secrets_or_retry(self):
        provider=Mock(side_effect=ValueError('secret-credential'))
        result=generate_analyst_brief(self.payload(),provider)
        self.assertNotIn('secret-credential',str(result));provider.assert_called_once()

    def test_structured_adapter_requests_prose_and_only_allowed_citations(self):
        p=self.payload();p['task']='performance_interpretation';candidate=simulated_brief(p)
        transport=Mock(return_value=io.BytesIO(json.dumps({'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(candidate)}]}]}).encode()))
        env={'PL_DNA_ENABLE_AZURE':'1','AZURE_OPENAI_BASE_URL':'https://demo.openai.azure.com/openai/v1/',
             'AZURE_OPENAI_API_KEY':'test-placeholder','AZURE_OPENAI_DEPLOYMENT':'test'}
        provider=create_provider_from_env(env,transport);self.assertEqual(provider(p),candidate)
        body=json.loads(transport.call_args.args[0].data)
        self.assertEqual(body['text']['format']['name'],'performance_interpretation')
        self.assertEqual(set(body['text']['format']['schema']['properties']),{'headline','narrative','evidence_ids'})
        self.assertFalse(body['store'])

    def test_ui_has_two_modes_and_one_ai_brief_no_duplicate_local_story(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        with patch('pl_dna.microsoft_provider.create_provider_from_env',return_value=Mock(side_effect=simulated_brief)) as factory:
            at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
            self.assertEqual(len(at.radio(key='data_source').options),2)
            factory.assert_not_called()
            at.button(key='season_generate_story').click().run()
            self.assertEqual(list(at.exception),[])
            self.assertEqual(len([c for c in at.caption if 'AI-written interpretation' in c.value]),1)
            self.assertFalse(any('Local calculated comparison' in c.value for c in at.caption))
            factory.return_value.assert_called_once()
            keys=list(load_current()['targets'])
            at.selectbox(key='current_target').select(keys[1]).run()
            self.assertFalse(any('AI-written interpretation' in c.value for c in at.caption))
            factory.return_value.assert_called_once()
