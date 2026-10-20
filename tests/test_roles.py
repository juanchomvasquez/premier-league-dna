"""Behavioral checks for the explicitly simulated role expansion."""
import json
import unittest
import pandas as pd
from pl_dna.roles import (
    ROLE_DEFINITIONS, PLAYERS, generate_role_events, analyze_role_player,
    score_role_profiles, score_role_features, build_role_story_input,
)


def row(eid, minute, kind, role='CB', player='Noah Bennett', completed=True,
        sequence=None):
    return dict(event_id=eid, minute=minute, event_type=kind,
                start_x=30., start_y=50., end_x=60., end_y=50.,
                completed=completed, sequence_id=sequence or eid,
                player=player, role=role, team='Test FC', synthetic=True,
                shot_outcome=None, sequence_minute=minute, action_tag=None,
                outcome=({'interception':'retained','block':'blocked','cross':'completed','recovery':'retained','pass':'completed'}.get(kind,'won') if completed else 'lost'))


def metrics(package):
    return {m['measurement']:m for m in package['measurements']}


class RoleGenerationTests(unittest.TestCase):
    def test_all_eight_roles_have_equal_opportunity_and_valid_source_schema(self):
        data = generate_role_events(42)
        expected = {'CB','FB','CM','CAM','ST','GK','WING','CDM'}
        self.assertEqual(set(ROLE_DEFINITIONS), expected)
        self.assertEqual(set(data['role']), expected)
        self.assertEqual(len(PLAYERS),8)
        self.assertTrue(set(PLAYERS).issubset(set(data['player'])))
        self.assertTrue(data['event_id'].is_unique)
        self.assertTrue(data['synthetic'].eq(True).all())
        self.assertTrue(data.groupby('player')['role'].nunique().eq(1).all())
        self.assertTrue(data.loc[data.player.isin(PLAYERS)].groupby('player')['sequence_id'].nunique().eq(60).all())
        self.assertTrue(data['minute'].between(0,90,inclusive='right').all())
        for column in ['start_x','start_y','end_x','end_y']:
            self.assertTrue(data[column].between(0,100).all())

    def test_original_non_cam_role_seed42_counts_are_preserved(self):
        expected={
            'Noah Bennett': [9,12,9,11,7],
            'Leo Serrano': [10,9,11,9,8],
            'Alex Morganfield': [13,11,11,6,14],
            'Sam Okafor': [13,16,9,7,10],
            'Ethan Vale': [6,6,7,21,7],
        }
        data=generate_role_events(42)
        for player,counts in expected.items():
            with self.subTest(player=player):
                report=analyze_role_player(data,player,0,90)
                self.assertEqual([m['count'] for m in report['measurements']],counts)

    def test_same_seed_exactly_reproduces_and_alternate_seed_changes_data(self):
        data = generate_role_events(42)
        pd.testing.assert_frame_equal(data, generate_role_events(42))
        self.assertFalse(data.equals(generate_role_events(43)))

    def test_each_role_returns_only_its_configured_metrics_and_selected_evidence(self):
        data = generate_role_events(42)
        for player, frame in data.loc[data.player.isin(PLAYERS)].groupby('player'):
            role = frame['role'].iloc[0]
            package = analyze_role_player(data, player, 30, 60)
            with self.subTest(role=role):
                self.assertEqual(package['role'], role)
                self.assertEqual(set(metrics(package)),
                                 set(ROLE_DEFINITIONS[role]['metrics']))
                selected = frame.loc[(frame.sequence_minute>30)&(frame.sequence_minute<=60)]
                self.assertEqual(package['recorded_events'], len(selected))
                self.assertEqual(package['action_sequences'], selected.sequence_id.nunique())
                for measurement in package['measurements']:
                    self.assertEqual(measurement['count'], len(set(measurement['event_ids'])))
                    self.assertTrue(set(measurement['event_ids']).issubset(set(selected.event_id)))


class RoleEvidenceTests(unittest.TestCase):
    def test_sequence_start_attribution_prevents_adjacent_window_double_count(self):
        first = row('first',29.99,'tackle',sequence='crossing')
        second = row('second',30.01,'interception',sequence='crossing')
        second['sequence_minute'] = 29.99
        data = pd.DataFrame([first,second])
        opening = analyze_role_player(data,'Noah Bennett',0,30)
        closing = analyze_role_player(data,'Noah Bennett',30,60)
        self.assertEqual(opening['action_sequences'],1)
        self.assertEqual(closing['action_sequences'],0)

    def test_inconsistent_role_is_rejected(self):
        data = pd.DataFrame([row('wrong',1,'tackle',role='ST')])
        with self.assertRaises(ValueError):
            analyze_role_player(data,'Noah Bennett',0,15)

    def test_chance_creation_requires_later_same_team_other_player_shot(self):
        for variant in ('valid','earlier','same_player','opponent','missing'):
            with self.subTest(variant=variant):
                key_pass = row('key',10,'pass',role='CAM',player='Diego Mercer',sequence='chance')
                key_pass['action_tag']='key_pass'
                receiver = row('shot',10.02,'shot',role='CAM',player='Receiver',sequence='chance',completed=False)
                receiver['sequence_minute']=10
                receiver['action_tag']='teammate_shot'
                if variant=='earlier': receiver['minute']=9.9
                if variant=='same_player': receiver['player']='Diego Mercer'
                if variant=='opponent': receiver['team']='Opposition FC'
                data=pd.DataFrame([key_pass] if variant=='missing' else [key_pass,receiver])
                result=metrics(analyze_role_player(data,'Diego Mercer',0,15))
                self.assertEqual(result['Chances created']['count'],int(variant=='valid'))
                self.assertEqual(result['Chances created']['supporting_event_ids'], ['shot'] if variant=='valid' else [])

    def test_replay_does_not_use_future_receiver_shot(self):
        key_pass=row('key',29.99,'pass',role='CAM',player='Diego Mercer',sequence='chance')
        key_pass['action_tag']='key_pass'
        receiver=row('shot',30.01,'shot',role='CAM',player='Receiver',sequence='chance',completed=False)
        receiver.update(sequence_minute=29.99,action_tag='teammate_shot')
        data=pd.DataFrame([key_pass,receiver])
        result=metrics(analyze_role_player(data,'Diego Mercer',0,30))
        self.assertEqual(result['Chances created']['count'],0)

    def test_explicit_defensive_outcome_overrides_inconsistent_completed_flag(self):
        data=pd.DataFrame([row('won',1,'tackle'),row('lost',2,'tackle')])
        data.loc[data.event_id.eq('lost'),'outcome']='lost'
        result=metrics(analyze_role_player(data,'Noah Bennett',0,15))
        self.assertEqual(result['Successful tackles']['event_ids'],['won'])

    def test_failed_defensive_actions_do_not_count_as_successful(self):
        role = 'CB'
        definition = ROLE_DEFINITIONS[role]
        for name, kind in definition['metrics'].items():
            with self.subTest(measurement=name):
                raw_kind = 'pass' if kind == 'progressive_pass' else kind
                data = pd.DataFrame([row('won',1,raw_kind),
                                     row('lost',2,raw_kind,completed=False)])
                result = metrics(analyze_role_player(data,'Noah Bennett',0,15))
                self.assertEqual(result[name]['count'],1)
                self.assertEqual(result[name]['event_ids'],['won'])

    def test_window_edges_and_other_player_do_not_contaminate(self):
        kind = next(iter(ROLE_DEFINITIONS['CB']['metrics'].values()))
        data = pd.DataFrame([row('start',30,kind), row('inside',31,kind),
                             row('end',45,kind), row('after',45.01,kind),
                             row('other',35,kind,player='Other Defender')])
        report = analyze_role_player(data,'Noah Bennett',30,45)
        self.assertEqual(report['recorded_events'],2)
        evidence = set().union(*(set(m['event_ids']) for m in report['measurements']))
        self.assertEqual(evidence,{'inside','end'})

    def test_unrelated_role_action_does_not_support_defender_measurements(self):
        own_types = set(ROLE_DEFINITIONS['CB']['metrics'].values())
        alien_types = set(ROLE_DEFINITIONS['ST']['metrics'].values()) - own_types
        self.assertTrue(alien_types)
        data = pd.DataFrame([row('alien',1,next(iter(alien_types)))])
        report = analyze_role_player(data,'Noah Bennett',0,15)
        self.assertEqual(report['recorded_events'],1)
        self.assertTrue(all(m['count']==0 for m in report['measurements']))

    def test_shared_sequence_counts_once_but_preserves_both_metric_events(self):
        kinds = list(ROLE_DEFINITIONS['CB']['metrics'].values())
        self.assertGreaterEqual(len(set(kinds)),2)
        data = pd.DataFrame([row('a',1,kinds[0],sequence='shared'),
                             row('b',1.02,kinds[1],sequence='shared')])
        report = analyze_role_player(data,'Noah Bennett',0,15)
        self.assertEqual(report['action_sequences'],1)
        self.assertEqual(report['recorded_events'],2)
        evidence = set().union(*(set(m['event_ids']) for m in report['measurements']))
        self.assertEqual(evidence,{'a','b'})


class MidfieldRoleSeparationTests(unittest.TestCase):
    def test_cam_winger_central_and_defensive_midfield_are_distinct(self):
        roles=['CAM','WING','CM','CDM']
        configured=[set(ROLE_DEFINITIONS[role]['metrics']) for role in roles]
        self.assertEqual(len({frozenset(values) for values in configured}),4)
        self.assertIn('Completed through balls',configured[0])
        self.assertIn('Completed crosses',configured[1])
        self.assertIn('Completed switches',configured[2])
        self.assertIn('Interceptions',configured[3])
        self.assertNotIn('Interceptions',configured[0])
        self.assertNotIn('Completed crosses',configured[0])
        self.assertNotIn('Successful take-ons',configured[3])

    def test_cam_through_ball_requires_tag_completion_and_forward_pass(self):
        good=row('through',1,'pass',role='CAM',player='Diego Mercer')
        good.update(start_x=60,end_x=85,action_tag='through_ball')
        untagged=dict(good,event_id='untagged',minute=2,sequence_minute=2,sequence_id='untagged',action_tag=None)
        failed=dict(good,event_id='failed',minute=3,sequence_minute=3,sequence_id='failed',completed=False,outcome='incomplete')
        wrong_type=dict(good,event_id='carry',minute=4,sequence_minute=4,sequence_id='carry',event_type='carry')
        backward=dict(good,event_id='backward',minute=5,sequence_minute=5,sequence_id='backward',end_x=40)
        result=metrics(analyze_role_player(pd.DataFrame([good,untagged,failed,wrong_type,backward]),'Diego Mercer',0,15))
        self.assertEqual(result['Completed through balls']['event_ids'],['through'])

    def test_cam_final_third_entry_requires_crossing_completed_boundary(self):
        boundary=100*2/3
        good=row('entry',1,'pass',role='CAM',player='Diego Mercer')
        good.update(start_x=50,end_x=boundary)
        below=dict(good,event_id='below',minute=2,sequence_minute=2,sequence_id='below',end_x=boundary-.01)
        already=dict(good,event_id='already',minute=3,sequence_minute=3,sequence_id='already',start_x=boundary,end_x=90)
        failed=dict(good,event_id='failed',minute=4,sequence_minute=4,sequence_id='failed',completed=False,outcome='incomplete')
        result=metrics(analyze_role_player(pd.DataFrame([good,below,already,failed]),'Diego Mercer',0,15))
        self.assertEqual(result['Passes entering final third']['event_ids'],['entry'])

    def test_winger_and_cdm_success_evidence_is_player_and_role_scoped(self):
        wing=row('wing_takeon',1,'take_on',role='WING',player='Mateo Silva')
        failed_wing=dict(wing,event_id='wing_failed',minute=2,sequence_minute=2,sequence_id='wing_failed',outcome='lost')
        cdm=row('cdm_recovery',3,'recovery',role='CDM',player='Owen Reed')
        failed_cdm=dict(cdm,event_id='cdm_failed',minute=4,sequence_minute=4,sequence_id='cdm_failed',outcome='not_retained')
        data=pd.DataFrame([wing,failed_wing,cdm,failed_cdm])
        wing_metrics=metrics(analyze_role_player(data,'Mateo Silva',0,15))
        cdm_metrics=metrics(analyze_role_player(data,'Owen Reed',0,15))
        self.assertEqual(wing_metrics['Successful take-ons']['event_ids'],['wing_takeon'])
        self.assertEqual(cdm_metrics['Ball recoveries']['event_ids'],['cdm_recovery'])
        self.assertNotIn('Ball recoveries',wing_metrics)
        self.assertNotIn('Successful take-ons',cdm_metrics)


class GoalkeeperEvidenceTests(unittest.TestCase):
    def keeper(self,eid,minute,kind,outcome,completed=True,sequence=None):
        item=row(eid,minute,kind,role='GK',player='Ethan Vale',completed=completed,sequence=sequence)
        item['outcome']=outcome
        return item

    def save_pair(self):
        save=self.keeper('save',10,'save','saved',sequence='save_sequence')
        save.update(start_x=5,end_x=5)
        shot=row('shot',9.99,'shot',role='ST',player='Opposing shooter',completed=False,sequence='save_sequence')
        shot.update(team='Opposition FC',action_tag='opponent_shot',outcome='saved',shot_outcome='saved',sequence_minute=10)
        return save,shot

    def test_save_requires_matching_prior_opposing_saved_shot(self):
        for variant in ['valid','missing','future','same_team','same_player','other_sequence','goal','failed_save']:
            with self.subTest(variant=variant):
                save,shot=self.save_pair()
                if variant=='future': shot['minute']=10.01
                if variant=='same_team': shot['team']=save['team']
                if variant=='same_player': shot.update(player='Ethan Vale',role='GK')
                if variant=='other_sequence': shot['sequence_id']='other'
                if variant=='goal': shot.update(outcome='goal',shot_outcome='goal')
                if variant=='failed_save': save.update(completed=False,outcome='conceded')
                data=pd.DataFrame([save] if variant=='missing' else [save,shot])
                report=analyze_role_player(data,'Ethan Vale',0,15)
                metric=metrics(report)['Saves']
                self.assertEqual(metric['count'],int(variant=='valid'))
                self.assertEqual(metric['event_ids'],['save'] if variant=='valid' else [])
                self.assertEqual(metric['supporting_event_ids'],['shot'] if variant=='valid' else [])

    def test_save_is_not_observed_before_its_timestamp(self):
        save,shot=self.save_pair()
        data=pd.DataFrame([save,shot])
        report=analyze_role_player(data,'Ethan Vale',0,9.995)
        self.assertEqual(report['recorded_events'],0)
        self.assertEqual(metrics(report)['Saves']['count'],0)

    def test_claim_and_sweeper_require_explicit_success_and_correct_geometry(self):
        claimed=self.keeper('claimed',1,'claim','claimed')
        missed=self.keeper('missed',2,'claim','missed')
        sweep=self.keeper('sweep',3,'sweeper_intervention','retained')
        inside=self.keeper('inside',4,'sweeper_intervention','retained')
        inside['start_x']=16
        failed=self.keeper('failed',5,'sweeper_intervention','missed',False)
        result=metrics(analyze_role_player(pd.DataFrame([claimed,missed,sweep,inside,failed]),'Ethan Vale',0,15))
        self.assertEqual(result['Successful claims']['event_ids'],['claimed'])
        self.assertEqual(result['Sweeper interventions']['event_ids'],['sweep'])

    def test_distribution_requires_completion_tag_and_distance(self):
        good=self.keeper('good',1,'pass','completed')
        good.update(start_x=5,end_x=35,start_y=50,end_y=50,action_tag='distribution')
        short=dict(good,event_id='short',minute=2,sequence_minute=2,sequence_id='short',end_x=34.9)
        failed=dict(good,event_id='failed',minute=3,sequence_minute=3,sequence_id='failed',completed=False)
        untagged=dict(good,event_id='untagged',minute=4,sequence_minute=4,sequence_id='untagged',action_tag=None)
        result=metrics(analyze_role_player(pd.DataFrame([good,short,failed,untagged]),'Ethan Vale',0,15))
        self.assertEqual(result['Completed long distribution']['event_ids'],['good'])
        self.assertIn('good',result['Completed progressive passes']['event_ids'])

    def test_keeper_metrics_exclude_unrelated_actions_and_other_keepers(self):
        unrelated=self.keeper('tackle',1,'tackle','won')
        own=self.keeper('own',2,'claim','claimed')
        other=dict(own,event_id='other',player='Other keeper',minute=3,sequence_minute=3)
        result=metrics(analyze_role_player(pd.DataFrame([unrelated,own,other]),'Ethan Vale',0,15))
        self.assertEqual(result['Successful claims']['event_ids'],['own'])
        evidence=set().union(*(set(m['event_ids']) for m in result.values()))
        self.assertEqual(evidence,{'own'})


class RolePayloadTests(unittest.TestCase):
    def test_all_twenty_four_invented_references_score_100_against_themselves(self):
        for role,definition in ROLE_DEFINITIONS.items():
            for name,rates in definition['profiles'].items():
                with self.subTest(role=role,reference=name):
                    result=score_role_features(role,dict(zip(definition['metrics'],rates)))
                    self.assertAlmostEqual(result.loc[name,'weighted_distance'],0)
                    self.assertAlmostEqual(result.loc[name,'experimental_resemblance_score'],100)

    def test_scores_only_compare_current_roles_profiles(self):
        data = generate_role_events(42)
        for player,frame in data.loc[data.player.isin(PLAYERS)].groupby('player'):
            role = frame['role'].iloc[0]
            scores = score_role_profiles(data,player,0,90)
            self.assertEqual(set(scores.index),set(ROLE_DEFINITIONS[role]['profiles']))
            self.assertTrue(scores['experimental_resemblance_score'].between(0,100).all())

    def test_empty_window_preserves_evidence_without_scores(self):
        kind = next(iter(ROLE_DEFINITIONS['CB']['metrics'].values()))
        data = pd.DataFrame([row('later',80,kind)])
        package = build_role_story_input(data,'Noah Bennett',0,15)
        self.assertEqual(package['action_sequences'],0)
        self.assertEqual(package['evidence']['recorded_events'],0)
        self.assertEqual(package['experimental_reference_scores'],[])
        json.dumps(package,allow_nan=False)

    def test_display_threshold_uses_sequences_not_event_rows(self):
        kind = next(iter(ROLE_DEFINITIONS['CB']['metrics'].values()))
        for count in (9,10):
            data = pd.DataFrame([row(f'e{i}',1+i/100,kind,sequence='shared')
                                 for i in range(12)] +
                                [row(f's{i}',2+i,kind) for i in range(count-1)])
            package = build_role_story_input(data,'Noah Bennett',0,15)
            self.assertEqual(package['action_sequences'],count)
            self.assertEqual(bool(package['experimental_reference_scores']),count>=10)
            self.assertEqual(package['evidence']['recorded_events'],count+11)
            json.dumps(package,allow_nan=False)


if __name__ == '__main__':
    unittest.main()
