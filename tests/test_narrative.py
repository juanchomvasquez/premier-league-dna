"""Adversarial narrative contract tests using only local fake providers."""
import copy
import unittest
from unittest.mock import Mock, patch
from pl_dna.roles import generate_role_events, build_role_story_input
from pl_dna.narrative import generate_narrative, validate_candidate


class NarrativeGroundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = build_role_story_input(generate_role_events(42),
                                             'Diego Mercer',0,90)

    def candidate(self):
        measurement=next(m for m in self.payload['evidence']['measurements'] if m['count']>0)
        return {'claims':[{key:copy.deepcopy(measurement[key])
                           for key in ['measurement','count','event_ids','supporting_event_ids']}]}

    def reject(self,candidate):
        with self.assertRaises(ValueError):
            validate_candidate(self.payload,candidate)
        provider=Mock(return_value=candidate)
        result=generate_narrative(self.payload,provider=provider)
        self.assertEqual(result['status'],'fallback')
        self.assertEqual(result['source'],'deterministic')
        self.assertTrue(result['text'])
        provider.assert_called_once()

    def test_valid_exact_claim_is_verified(self):
        candidate=self.candidate()
        normalized=validate_candidate(self.payload,candidate)
        self.assertEqual(len(normalized),1)
        provider=Mock(return_value=candidate)
        result=generate_narrative(self.payload,provider=provider)
        self.assertEqual(result['status'],'verified')
        self.assertEqual(result['source'],'model-selected')
        self.assertTrue(result['text'])
        provider.assert_called_once()

    def test_provider_cannot_mutate_the_trusted_payload(self):
        original=copy.deepcopy(self.payload)
        def malicious_provider(incoming):
            incoming['evidence']['measurements'][0]['count']=999
            incoming['evidence']['measurements'][0]['event_ids']=['FORGED']*999
            measurement=incoming['evidence']['measurements'][0]
            return {'claims':[{key:measurement[key] for key in
                              ['measurement','count','event_ids','supporting_event_ids']}]}
        result=generate_narrative(self.payload,provider=malicious_provider)
        self.assertEqual(result['status'],'fallback')
        self.assertNotIn('999',result['text'])
        self.assertEqual(self.payload,original)

    def test_count_change_is_rejected(self):
        candidate=self.candidate();candidate['claims'][0]['count']+=1
        self.reject(candidate)

    def test_foreign_primary_event_is_rejected(self):
        candidate=self.candidate();candidate['claims'][0]['event_ids'][0]='FOREIGN_EVENT'
        self.reject(candidate)

    def test_supported_count_with_missing_evidence_is_rejected(self):
        candidate=self.candidate();candidate['claims'][0]['event_ids']=[]
        self.reject(candidate)

    def test_duplicate_primary_evidence_is_rejected(self):
        candidate=self.candidate()
        candidate['claims'][0]['event_ids'].append(candidate['claims'][0]['event_ids'][0])
        self.reject(candidate)

    def test_unsupported_metric_is_rejected(self):
        candidate=self.candidate();candidate['claims'][0]['measurement']='Expected goals'
        self.reject(candidate)

    def test_missing_claim_fields_are_rejected(self):
        for field in ['measurement','count','event_ids','supporting_event_ids']:
            with self.subTest(field=field):
                candidate=self.candidate();del candidate['claims'][0][field]
                self.reject(candidate)

    def test_boolean_float_and_string_counts_are_rejected(self):
        for count in [True,1.0,'1',None]:
            with self.subTest(count=count):
                candidate=self.candidate();candidate['claims'][0]['count']=count
                self.reject(candidate)

    def test_missing_empty_and_duplicate_claims_are_rejected(self):
        self.reject({})
        self.reject({'claims':[]})
        candidate=self.candidate();candidate['claims']*=2
        self.reject(candidate)

    def test_too_many_claims_are_rejected(self):
        candidate={'claims':[{key:copy.deepcopy(m[key]) for key in
                            ['measurement','count','event_ids','supporting_event_ids']}
                            for m in self.payload['evidence']['measurements'][:4]]}
        self.reject(candidate)

    def test_fabricated_scores_and_probabilities_are_rejected(self):
        for key,value in [('score',99),('probability',.98),('legend_similarity','99% Gerrard')]:
            for target in ['top','claim']:
                with self.subTest(key=key,target=target):
                    candidate=self.candidate()
                    destination=candidate if target=='top' else candidate['claims'][0]
                    destination[key]=value
                    self.reject(candidate)

    def test_arbitrary_model_prose_cannot_reach_rendered_text(self):
        malicious='He became99% Gerrard because the manager changed tactics.'
        for candidate in [malicious,{'text':malicious},
                          dict(self.candidate(),text=malicious)]:
            self.reject(candidate)
            result=generate_narrative(self.payload,provider=lambda p:candidate)
            self.assertNotIn(malicious,result['text'])

    def test_forged_and_missing_secondary_chance_evidence_is_rejected(self):
        measurement=next(m for m in self.payload['evidence']['measurements']
                         if m['measurement']=='Chances created')
        self.assertTrue(measurement['supporting_event_ids'])
        for ids in [[],['FOREIGN_SHOT']]:
            candidate={'claims':[copy.deepcopy(measurement)]}
            candidate['claims'][0]['supporting_event_ids']=ids
            self.reject(candidate)


class NarrativeFallbackTests(unittest.TestCase):
    def setUp(self):
        self.data=generate_role_events(42)
        self.payload=build_role_story_input(self.data,'Alex Morganfield',0,90)

    def test_default_path_does_not_open_network_connections(self):
        with patch('socket.create_connection',side_effect=AssertionError('network forbidden')) as connection:
            result=generate_narrative(self.payload)
        connection.assert_not_called()
        self.assertEqual(result['status'],'fallback')

    def test_no_provider_uses_deterministic_fallback(self):
        result=generate_narrative(self.payload)
        self.assertEqual(result['status'],'fallback')
        self.assertEqual(result['source'],'deterministic')
        self.assertTrue(result['text'])
        self.assertIn('synthetic',result['text'].lower())

    def test_provider_exception_returns_grounded_fallback(self):
        provider=Mock(side_effect=RuntimeError('offline secret credential'))
        result=generate_narrative(self.payload,provider=provider)
        self.assertEqual(result['status'],'fallback')
        self.assertTrue(result['text'])
        self.assertNotIn('secret credential',result['text'])
        provider.assert_called_once()

    def test_empty_sample_does_not_invent_activity_or_style(self):
        earliest=float(self.data.loc[self.data.player.eq('Alex Morganfield'),'sequence_minute'].min())
        payload=build_role_story_input(self.data,'Alex Morganfield',0,earliest/2)
        result=generate_narrative(payload)
        self.assertEqual(result['status'],'fallback')
        self.assertTrue(result['text'])
        self.assertNotIn('no activity',result['text'].lower())
        self.assertFalse(payload['experimental_reference_scores'])

    def test_keeper_save_secondary_shot_tampering_is_rejected(self):
        payload=build_role_story_input(self.data,'Ethan Vale',0,90)
        save=next(m for m in payload['evidence']['measurements'] if m['measurement']=='Saves')
        self.assertGreater(save['count'],0)
        self.assertTrue(save['supporting_event_ids'])
        candidate={'claims':[copy.deepcopy(save)]}
        candidate['claims'][0]['supporting_event_ids']=['FOREIGN_SHOT']
        with self.assertRaises(ValueError):
            validate_candidate(payload,candidate)
        result=generate_narrative(payload,provider=lambda p:candidate)
        self.assertEqual(result['status'],'fallback')

    def test_cam_new_spanish_metrics_are_translated(self):
        payload=build_role_story_input(self.data,'Diego Mercer',0,90)
        translations={'Completed through balls':'pases filtrados completados',
                      'Passes entering final third':'pases que entran en el último tercio'}
        for metric,translation in translations.items():
            with self.subTest(metric=metric):
                claim=next(m for m in payload['evidence']['measurements'] if m['measurement']==metric)
                result=generate_narrative(payload,provider=lambda p:{'claims':[claim]},language='Spanish')
                self.assertEqual(result['status'],'verified')
                self.assertIn(translation,result['text'])
                self.assertNotIn(metric.lower(),result['text'])

    def test_keeper_spanish_metrics_are_translated(self):
        payload=build_role_story_input(self.data,'Ethan Vale',0,90)
        measurements=payload['evidence']['measurements']
        translations={'Saves':'paradas','Successful claims':'balones atrapados con éxito',
                      'Sweeper interventions':'intervenciones fuera del área',
                      'Completed long distribution':'envíos largos completados'}
        for metric,translation in translations.items():
            with self.subTest(metric=metric):
                claim=next(m for m in measurements if m['measurement']==metric)
                result=generate_narrative(payload,provider=lambda p:{'claims':[claim]},language='Spanish')
                self.assertEqual(result['status'],'verified')
                self.assertIn(translation,result['text'])
                self.assertNotIn(metric.lower(),result['text'])

    def test_spanish_supported_without_provider_or_external_calls(self):
        result=generate_narrative(self.payload,language='Spanish')
        self.assertEqual(result['status'],'fallback')
        self.assertTrue(result['text'])
        self.assertTrue(any(word in result['text'].lower() for word in ['sintétic','demostración']))


if __name__=='__main__':
    unittest.main()
