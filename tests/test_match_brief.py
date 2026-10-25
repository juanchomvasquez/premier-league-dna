import copy
import io
import json
import unittest
from unittest.mock import Mock
from pl_dna.match_brief import build_match_brief, generate_match_brief, validate_brief
from pl_dna.microsoft_provider import create_provider_from_env
from pl_dna.roles import generate_role_events, PLAYERS, analyze_role_player


class MatchBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate_role_events(42)

    def payload(self):
        return build_match_brief(self.data, 'Alex Morganfield', 90)

    def test_all_positions_use_equal_nonoverlapping_past_windows(self):
        for player in PLAYERS:
            with self.subTest(player=player):
                payload = build_match_brief(self.data, player, 90)
                self.assertEqual(payload['previous'], analyze_role_player(self.data, player, 60, 75))
                self.assertEqual(payload['recent'], analyze_role_player(self.data, player, 75, 90))
                previous = {eid for m in payload['previous']['measurements'] for eid in m['event_ids']}
                recent = {eid for m in payload['recent']['measurements'] for eid in m['event_ids']}
                self.assertFalse(previous & recent)

    def test_early_or_sparse_windows_never_call_provider(self):
        provider = Mock()
        for end in (1, 15, 29):
            result = generate_match_brief(build_match_brief(self.data, 'Sam Okafor', end), provider)
            self.assertEqual(result['status'], 'insufficient')
        empty = self.data.copy()
        empty['sequence_minute'] = 1.0
        result = generate_match_brief(build_match_brief(empty, 'Sam Okafor', 90), provider)
        self.assertEqual(result['status'], 'insufficient')
        provider.assert_not_called()

    def test_no_provider_is_preview_not_an_ai_result(self):
        result = generate_match_brief(self.payload())
        self.assertEqual(result['status'], 'preview')
        self.assertIsNone(result['brief'])

    def test_valid_story_uses_exact_counts_and_evidence(self):
        payload = self.payload()
        ids = [c['id'] for c in payload['comparisons']]
        provider = Mock(return_value={'lead': ids[0], 'support': ids[1] if len(ids) > 1 else None})
        result = generate_match_brief(payload, provider)
        self.assertEqual(result['status'], 'verified')
        selected = result['brief']['evidence'][0]
        self.assertIn(f"{selected['before']['count']} → {selected['after']['count']}", result['brief']['facts'][0])
        self.assertEqual(result['brief']['period'], '(60, 75] → (75, 90]')
        self.assertTrue(result['brief']['watch'])
        provider.assert_called_once()

    def test_forged_or_repeated_ids_and_added_prose_are_rejected(self):
        payload = self.payload()
        lead = payload['comparisons'][0]['id']
        for candidate in ({'lead': 'FORGED', 'support': None}, {'lead': lead, 'support': lead},
                          {'lead': lead, 'support': None, 'text': 'Better than Lampard'},
                          {'lead': [], 'support': None}, {'lead': lead, 'support': {}}):
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_brief(payload, candidate)
                result = generate_match_brief(payload, lambda p: candidate)
                self.assertEqual(result['status'], 'fallback')
                self.assertIsNone(result['brief'])

    def test_provider_cannot_modify_calculated_facts(self):
        payload = self.payload()
        original = copy.deepcopy(payload)
        def provider(incoming):
            incoming['comparisons'][0]['after']['count'] = 9999
            return {'lead': incoming['comparisons'][0]['id'], 'support': None}
        result = generate_match_brief(payload, provider)
        self.assertNotIn('9999', result['brief']['headline'])
        self.assertEqual(payload, original)

    def test_failure_does_not_expose_transport_details(self):
        result = generate_match_brief(self.payload(), Mock(side_effect=RuntimeError('secret key')))
        self.assertEqual(result['status'], 'fallback')
        self.assertNotIn('secret key', result['reason'])

    def test_adapter_sends_editorial_task_once_without_retry(self):
        calls = []
        candidate = {'lead': self.payload()['comparisons'][0]['id'], 'support': None}
        def transport(request, timeout):
            calls.append(request)
            return io.BytesIO(json.dumps({'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': json.dumps(candidate)}]}]}).encode())
        provider = create_provider_from_env({'PL_DNA_ENABLE_AZURE': '1',
            'AZURE_OPENAI_BASE_URL': 'https://example.services.ai.azure.com/openai/v1/',
            'AZURE_OPENAI_DEPLOYMENT': 'demo', 'AZURE_OPENAI_API_KEY': 'placeholder'}, transport)
        self.assertEqual(generate_match_brief(self.payload(), provider)['status'], 'verified')
        self.assertEqual(len(calls), 1)
        body = json.loads(calls[0].data)
        self.assertIn('broadcast research editor', body['input'])
        self.assertFalse(body['store'])

class MatchBriefDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.payload = build_match_brief(generate_role_events(42), 'Alex Morganfield', 90)

    def test_http_failures_are_distinct_and_never_show_private_error_text(self):
        from urllib.error import HTTPError
        config = {'PL_DNA_ENABLE_AZURE': '1',
                  'AZURE_OPENAI_BASE_URL': 'https://demo.services.ai.azure.com/openai/v1/',
                  'AZURE_OPENAI_API_KEY': 'private-placeholder', 'AZURE_OPENAI_DEPLOYMENT': 'demo'}
        for status in (400, 401, 403, 404, 429, 500):
            transport = Mock(side_effect=HTTPError('https://private.example', status, 'private-placeholder', {}, None))
            provider = create_provider_from_env(config, transport)
            result = generate_match_brief(self.payload, provider)
            self.assertEqual(result['status'], 'fallback')
            self.assertNotIn('private-placeholder', result['reason'])
            self.assertNotIn('private.example', result['reason'])
            self.assertIn('No automatic retry', result['reason'])
            if status < 500:
                self.assertIn(str(status), result['reason'])
            transport.assert_called_once()

    def test_malformed_json_is_not_reported_as_a_bad_evidence_id(self):
        from pl_dna.microsoft_provider import ProviderError
        result = generate_match_brief(self.payload, Mock(side_effect=ProviderError('invalid_json')))
        self.assertIn('JSON format', result['reason'])
        result = generate_match_brief(self.payload, lambda p: {'lead':'FORGED','support':None})
        self.assertIn('change IDs', result['reason'])

    def test_strict_response_schema_only_allows_supplied_ids(self):
        config = {'PL_DNA_ENABLE_AZURE': '1',
                  'AZURE_OPENAI_BASE_URL': 'https://demo.services.ai.azure.com/openai/v1/',
                  'AZURE_OPENAI_API_KEY': 'placeholder', 'AZURE_OPENAI_DEPLOYMENT': 'demo'}
        requests = []
        def transport(request, timeout):
            requests.append(request)
            return io.BytesIO(json.dumps({'output':[{'type':'message','content':[{'type':'output_text',
                'text':json.dumps({'lead':self.payload['comparisons'][0]['id'],'support':None})}]}]}).encode())
        result = generate_match_brief(self.payload, create_provider_from_env(config, transport))
        self.assertEqual(result['status'], 'verified')
        format = json.loads(requests[0].data)['text']['format']
        self.assertTrue(format['strict'])
        self.assertEqual(format['type'], 'json_schema')
        self.assertFalse(format['schema']['additionalProperties'])
        self.assertEqual(format['schema']['properties']['lead']['enum'], [c['id'] for c in self.payload['comparisons']])
