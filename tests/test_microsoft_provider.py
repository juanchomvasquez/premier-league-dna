import io
import json
import unittest
from pl_dna.microsoft_provider import create_provider_from_env


class ProviderTests(unittest.TestCase):
    def config(self):
        return {'PL_DNA_ENABLE_AZURE': '1',
                'AZURE_OPENAI_BASE_URL': 'https://demo.openai.azure.com/openai/v1/',
                'AZURE_OPENAI_API_KEY': 'test-placeholder', 'AZURE_OPENAI_DEPLOYMENT': 'demo'}

    def test_disabled_or_non_microsoft_configuration_never_calls_transport(self):
        calls = []
        for env in ({}, {**self.config(), 'AZURE_OPENAI_BASE_URL': 'https://example.com/openai/v1/'}):
            with self.assertRaises(ValueError):
                create_provider_from_env(env, lambda *a, **kw: calls.append(a))
        self.assertEqual(calls, [])

    def test_construction_is_local_and_explicit_call_uses_expected_request(self):
        calls = []
        candidate = {'claims': []}
        def transport(request, timeout):
            calls.append((request, timeout))
            return io.BytesIO(json.dumps({'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': json.dumps(candidate)}]}]}).encode())
        provider = create_provider_from_env(self.config(), transport)
        self.assertEqual(calls, [])
        self.assertEqual(provider({'evidence': {'measurements': []}}), candidate)
        request, timeout = calls[0]
        self.assertEqual(request.full_url, 'https://demo.openai.azure.com/openai/v1/responses')
        self.assertEqual(timeout, 30)
        body = json.loads(request.data)
        self.assertFalse(body['store'])
        self.assertEqual(body['model'], 'demo')

    def test_missing_or_invalid_output_is_rejected(self):
        for body in ({'output': []}, {'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': 'not JSON'}]}]}):
            provider = create_provider_from_env(self.config(), lambda *a, **kw: io.BytesIO(json.dumps(body).encode()))
            with self.assertRaises(ValueError):
                provider({})
