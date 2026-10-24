import copy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import numpy as np

from pl_dna.legend_blend import (fit_blend, load_midfield_study,
    build_blend_payload, generate_blend_story, validate_story)
from pl_dna.microsoft_provider import create_provider_from_env
from pl_dna.recorded_events import METRICS
from tools.build_midfield_study import observed_by


class BlendTests(unittest.TestCase):
    def setUp(self):
        self.study = load_midfield_study()
        self.key = next(iter(self.study['targets']))
        self.payload = build_blend_payload(self.study, self.key, 90)

    def test_known_mixture_and_boundary_are_recovered(self):
        refs = self.study['references']
        expected = [.2, .3, .5]
        target = {'rates': {k: sum(w*r['rates'][k] for w, r in zip(expected, refs.values())) for k in METRICS}}
        result = fit_blend(target, refs)
        np.testing.assert_allclose(list(result['weights'].values()), expected, atol=1e-10)
        self.assertAlmostEqual(result['rmse'], 0)
        self.assertEqual(sum(result['percentages'].values()), 100)
        for name in refs:
            pure = fit_blend(refs[name], refs)
            self.assertEqual(pure['percentages'][name], 100)
            self.assertAlmostEqual(pure['rmse'], 0)

    def test_missing_and_indistinguishable_rates_fail_instead_of_becoming_zero(self):
        refs = copy.deepcopy(self.study['references'])
        target = self.payload['target']
        bad = copy.deepcopy(target)
        bad['rates'][next(iter(METRICS))] = None
        with self.assertRaises(ValueError):
            fit_blend(bad, refs)
        for n in refs:
            refs[n]['rates'] = target['rates']
        with self.assertRaises(ValueError):
            fit_blend(target, refs)

    def test_real_snapshots_reconcile_and_targets_are_held_out(self):
        refs = self.study['references']
        self.assertEqual([r['appearances'] for r in refs.values()], [2, 2, 1])
        self.assertEqual([r['actions'] for r in refs.values()], [111, 131, 56])
        reference_matches = {mid for r in refs.values() for mid in r['match_ids']}
        for entry in self.study['targets'].values():
            self.assertNotIn(entry['match_id'], reference_matches)
            previous = {k: 0 for k in METRICS}
            for snapshot in entry['snapshots'].values():
                for k in METRICS:
                    self.assertGreaterEqual(snapshot['counts'][k], previous[k])
                    previous[k] = snapshot['counts'][k]
                    if snapshot['actions']:
                        self.assertAlmostEqual(snapshot['rates'][k], 100*snapshot['counts'][k]/snapshot['actions'])
        broken = copy.deepcopy(self.study)
        broken['references']['Frank Lampard']['match_ids'].append(broken['targets'][self.key]['match_id'])
        with self.assertRaises(ValueError):
            build_blend_payload(broken, self.key, 90)

    def test_future_shot_cannot_support_an_earlier_assist(self):
        events = [dict(id='pass', period=1, minute=10, type={'name': 'Pass'},
                       **{'pass': {'assisted_shot_id': 'shot'}}),
                  dict(id='shot', period=1, minute=11, type={'name': 'Shot'}),
                  dict(id='added', period=1, minute=47, type={'name': 'Shot'}),
                  dict(id='second', period=2, minute=48, type={'name': 'Shot'})]
        early = observed_by(events, 11)
        self.assertEqual([e['id'] for e in early], ['pass'])
        self.assertNotIn('assisted_shot_id', early[0]['pass'])
        self.assertEqual(events[0]['pass']['assisted_shot_id'], 'shot')
        self.assertEqual(observed_by(events, 12)[0]['pass']['assisted_shot_id'], 'shot')
        self.assertEqual([e['id'] for e in observed_by(events, 45)], ['pass', 'shot', 'added'])
        self.assertEqual(len(observed_by(events, 90)), 4)

    def test_provider_cannot_change_percentages_or_mutate_trusted_evidence(self):
        p = self.payload
        candidate = {'angle': 'mixed_profile', 'lead': p['evidence'][0]['id'], 'support': None}
        def provider(data):
            data['fit']['percentages']['Frank Lampard'] = 999
            data['evidence'][0]['sentence'] = 'Forged sentence'
            return candidate
        result = generate_blend_story(p, provider)
        self.assertEqual(result['status'], 'verified')
        self.assertNotIn('999', result['text'])
        self.assertNotIn('Forged', result['text'])
        self.assertIn('66% Lampard', result['text'])
        bad = dict(candidate, percentage=999)
        with self.assertRaises(ValueError):
            validate_story(p, bad)
        bad = dict(candidate, lead='invented')
        self.assertEqual(generate_blend_story(p, lambda _: bad)['status'], 'fallback')
        low = build_blend_payload(self.study, self.key, 1)
        mock = Mock()
        self.assertEqual(generate_blend_story(low, mock)['status'], 'insufficient')
        mock.assert_not_called()

    def test_adapter_uses_blend_schema_and_only_one_request(self):
        p = self.payload
        candidate = {'angle': 'mixed_profile', 'lead': p['evidence'][0]['id'], 'support': None}
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps({'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps(candidate)}]}]}).encode()
        transport = Mock(return_value=response)
        provider = create_provider_from_env({'PL_DNA_ENABLE_AZURE': '1',
            'AZURE_OPENAI_BASE_URL': 'https://example.openai.azure.com/openai/v1/',
            'AZURE_OPENAI_API_KEY': 'test-key', 'AZURE_OPENAI_DEPLOYMENT': 'test-deployment'}, transport)
        self.assertEqual(generate_blend_story(p, provider)['status'], 'verified')
        transport.assert_called_once()
        sent = json.loads(transport.call_args.args[0].data)
        self.assertEqual(sent['text']['format']['name'], 'legend_blend')
        self.assertFalse(sent['store'])
        self.assertEqual(set(sent['text']['format']['schema']['properties']), {'angle', 'lead', 'support'})
        self.assertNotIn('test-key', sent['input'])

    def test_ui_never_calls_azure_on_control_changes_and_hides_stale_story(self):
        from streamlit.testing.v1 import AppTest
        provider = Mock(side_effect=lambda p: {'angle': 'closest_sample', 'lead': p['evidence'][0]['id'], 'support': None})
        with patch('pl_dna.microsoft_provider.create_provider_from_env', return_value=provider) as factory:
            at = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'), default_timeout=30).run()
            self.assertEqual(list(at.exception), [])
            factory.assert_not_called()
            at.button(key='generate_legend_story').click().run()
            self.assertEqual(list(at.exception), [])
            self.assertEqual(provider.call_count, 1)
            self.assertTrue(any('Microsoft-selected story' in c.value for c in at.caption))
            self.assertFalse(any(r.key == 'audience' for r in at.radio))
            at.selectbox(key='blend_legend').select('Paul Scholes').run()
            self.assertTrue(any('Microsoft-selected story' in c.value for c in at.caption))
            at.slider(key='blend_minute').set_value(60).run()
            at.selectbox(key='blend_target').select(list(self.study['targets'])[1]).run()
            self.assertEqual(list(at.exception), [])
            self.assertEqual(provider.call_count, 1)
            self.assertFalse(any('Microsoft-selected story' in c.value for c in at.caption))


if __name__ == '__main__':
    unittest.main()
