"""Independent behavioral checks. Run: python -m unittest discover -s tests -v."""
import unittest
import numpy as np
import pandas as pd
from pl_dna.engine import (
    analyze_player, generate_midfield_events, calculate_sequence_blend,
    build_style_features, score_style_profiles, reference_profiles,
    build_story_input,
)


def event(eid, minute, kind='pass', sx=40, sy=50, ex=70, ey=50,
          completed=True, sequence=None, player='Test Player'):
    return dict(event_id=eid, minute=minute, event_type=kind,
                start_x=sx, start_y=sy, end_x=ex, end_y=ey,
                completed=completed, sequence_id=sequence or eid,
                player=player, team='Test FC', synthetic=True,
                shot_outcome=None)


def measurements(report):
    return {row['measurement']: row for row in report['measurements']}


class EvidenceTests(unittest.TestCase):
    def test_window_is_start_exclusive_end_inclusive_and_player_scoped(self):
        data = pd.DataFrame([event('start', 30), event('inside', 31),
                             event('end', 45), event('after', 45.01),
                             event('other', 35, player='Other Player')])
        report = analyze_player(data, 'Test Player', 30, 45)
        self.assertEqual(report['recorded_events'], 2)
        self.assertEqual(measurements(report)['Completed passes']['event_ids'],
                         ['inside', 'end'])

    def test_failed_pass_is_recorded_but_does_not_support_completed_metrics(self):
        report = analyze_player(pd.DataFrame([event('failed', 4, completed=False)]),
                                'Test Player', 0, 15)
        self.assertEqual(report['recorded_events'], 1)
        self.assertTrue(all(m['count'] == 0 for m in report['measurements']))

    def test_progression_uses_distance_reduction_not_just_forward_x(self):
        data = pd.DataFrame([event('threshold', 1, sx=40, ex=55),
                             event('below', 2, sx=40, ex=54.9),
                             event('wide', 3, sx=38, sy=80, ex=52, ey=15)])
        result = measurements(analyze_player(data, 'Test Player', 0, 15))
        self.assertEqual(result['Progressive passes']['event_ids'], ['threshold'])
        self.assertIn('wide', result['Completed switches']['event_ids'])

    def test_box_arrival_requires_entry_from_outside(self):
        data = pd.DataFrame([event('entry', 1, 'box_arrival', sx=78, ex=90),
                             event('already', 2, 'box_arrival', sx=85, ex=90),
                             event('wide', 3, 'box_arrival', sx=78, ex=90, ey=80)])
        result = measurements(analyze_player(data, 'Test Player', 0, 15))
        self.assertEqual(result['Box arrivals']['event_ids'], ['entry'])

    def test_shots_count_even_when_not_goals(self):
        data = pd.DataFrame([event('miss', 1, 'shot', completed=False),
                             event('goal', 2, 'shot')])
        self.assertEqual(measurements(analyze_player(data, 'Test Player'))['Shots']['count'], 2)

    def test_invalid_window_and_unknown_player(self):
        data = pd.DataFrame([event('one', 1)])
        with self.assertRaises(ValueError):
            analyze_player(data, 'Test Player', 15, 15)
        with self.assertRaises(ValueError):
            analyze_player(data, 'Missing Player')

    def test_empty_window_has_no_evidence_and_no_invented_rates(self):
        data = pd.DataFrame([event('one', 60)])
        report = analyze_player(data, 'Test Player', 0, 15)
        self.assertEqual(report['recorded_events'], 0)
        self.assertTrue(all(m['count'] == 0 and m['event_ids'] == []
                            for m in report['measurements']))
        features = build_style_features(data, 'Test Player', 0, 15)
        self.assertEqual(features['action_sequences'], 0)
        blend = calculate_sequence_blend(data, 'Test Player', 0, 15)
        self.assertTrue(blend['sequence_coverage_pct'].isna().all())


class SequenceTests(unittest.TestCase):
    def test_related_attack_rows_count_once_in_coverage_denominator(self):
        data = pd.DataFrame([
            event('arrival', 1, 'box_arrival', sx=78, ex=90, sequence='attack'),
            event('touch', 1.02, 'touch', sx=90, ex=90, sequence='attack'),
            event('shot', 1.04, 'shot', sx=90, ex=100, sequence='attack'),
            event('failed', 2, completed=False, sequence='other')])
        blend = calculate_sequence_blend(data, 'Test Player', 0, 15)
        row = blend.loc[blend['profile'].str.startswith('Lampard')].iloc[0]
        self.assertEqual(row['total_sequences'], 2)
        self.assertEqual(row['supporting_sequences'], 1)
        self.assertEqual(row['sequence_coverage_pct'], 50)
        features = build_style_features(data, 'Test Player', 0, 15)
        self.assertEqual(features['Shots'], 50)
        self.assertEqual(features['Box arrivals'], 50)

    def test_one_pass_can_support_multiple_dimensions(self):
        data = pd.DataFrame([event('pass', 1)])
        blend = calculate_sequence_blend(data, 'Test Player', 0, 15)
        coverage = dict(zip(blend['profile'], blend['sequence_coverage_pct']))
        self.assertEqual(next(v for k,v in coverage.items() if k.startswith('Gerrard')), 100)
        self.assertEqual(next(v for k,v in coverage.items() if k.startswith('Scholes')), 100)
        self.assertEqual(sum(coverage.values()), 200)

    def test_every_generated_evidence_id_has_correct_player_and_time(self):
        data = generate_midfield_events()
        for player in data['player'].unique():
            for start,end in [(0,30), (30,60), (60,90), (28,43)]:
                report = analyze_player(data, player, start, end)
                valid = data.loc[(data.player == player) & (data.minute > start)
                                 & (data.minute <= end)]
                for metric in report['measurements']:
                    self.assertEqual(metric['count'], len(set(metric['event_ids'])))
                    self.assertTrue(set(metric['event_ids']).issubset(set(valid.event_id)))


class StoryPayloadTests(unittest.TestCase):
    def test_threshold_hides_scores_but_retains_evidence(self):
        for count in (0, 9, 10):
            with self.subTest(sequence_count=count):
                # One later event keeps the player known for an empty window.
                data = pd.DataFrame([event(str(i), i + 1) for i in range(count)]
                                    + [event('later', 80)])
                package = build_story_input(data, 'Test Player', 0, 15)
                self.assertEqual(package['action_sequences'], count)
                self.assertEqual(package['evidence']['recorded_events'], count)
                self.assertEqual(len(package['experimental_reference_scores']),
                                 3 if count >= 10 else 0)
                self.assertEqual(package['window'],
                                 {'start_exclusive': 0, 'end_inclusive': 15})

    def test_story_package_serializes_as_standard_json(self):
        import json
        package = build_story_input(generate_midfield_events(),
                                    'Alex Morganfield', 28, 43,
                                    view='Last 15 minutes')
        encoded = json.dumps(package, allow_nan=False)
        restored = json.loads(encoded)
        self.assertEqual(restored['action_sequences'], 14)
        self.assertEqual(restored['evidence']['recorded_events'], 16)
        self.assertEqual(restored['experimental_reference_scores'][0],
                         {'reference':'Gerrard-inspired', 'experimental_score':83.2})


class ModelTests(unittest.TestCase):
    def test_seed_reproduces_exact_dataset_and_other_seed_changes_it(self):
        first = generate_midfield_events(42)
        pd.testing.assert_frame_equal(first, generate_midfield_events(42))
        self.assertFalse(first.equals(generate_midfield_events(43)))
        self.assertTrue(first.event_id.is_unique)
        self.assertTrue(first.groupby('player').sequence_id.nunique().eq(60).all())

    def test_every_reference_scores_100_against_itself(self):
        for name, reference in reference_profiles.iterrows():
            result = score_style_profiles(reference)
            self.assertAlmostEqual(result.loc[name, 'experimental_resemblance_score'], 100)
            self.assertAlmostEqual(result.loc[name, 'weighted_distance'], 0)

    def test_nonfinite_features_are_rejected(self):
        vector = reference_profiles.iloc[0].copy()
        vector.iloc[0] = np.nan
        with self.assertRaises(ValueError):
            score_style_profiles(vector)

    def test_seed42_regression_matches_verified_notebook_scores(self):
        features = build_style_features(generate_midfield_events(42),
                                        'Alex Morganfield', 0, 90)
        result = score_style_profiles(pd.Series(features))
        expected = {'Gerrard-inspired':77.9, 'Lampard-inspired':70.9,
                    'Scholes-inspired':75.9}
        for name, score in expected.items():
            self.assertEqual(round(result.loc[name, 'experimental_resemblance_score'], 1), score)


if __name__ == '__main__':
    unittest.main()
