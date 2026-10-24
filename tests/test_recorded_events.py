"""Definitions, source reconciliation, missingness and self-inclusion boundaries."""
import unittest
from copy import deepcopy
from unittest.mock import Mock,patch
import xml.etree.ElementTree as ET
from pl_dna.recorded_events import player_profile,pooled_profile,load_study,comparison_wheel,METRICS
from pl_dna.career import CAREERS,club_shares,career_html,club_background


def event(eid,kind,player=1,period=1,**extra):
    return dict(id=eid,type={'name':kind},period=period,player={'id':player},**extra)


class RecordedEventsTests(unittest.TestCase):
    def test_same_action_counting_policy_includes_added_time_but_not_extra_time(self):
        es=[event('s','Shot',minute=46,shot={'type':{'name':'Open Play'},'outcome':{'name':'Goal'}}),
            event('pen','Shot',shot={'type':{'name':'Penalty'},'outcome':{'name':'Goal'}}),
            event('p','Pass',location=[100,40],**{'pass':{'end_location':[102,18],'assisted_shot_id':'s'}}),
            event('q','Pass',location=[100,40],**{'pass':{'end_location':[119,40],'outcome':{'name':'Incomplete'}}}),
            event('f','Pass',location=[30,10],**{'pass':{'end_location':[40,10]}}),
            event('d','Dribble',dribble={'outcome':{'name':'Complete'}}),
            event('carry','Carry'),event('receipt','Ball Receipt*'),
            event('other','Shot',player=2,shot={'type':{'name':'Open Play'},'outcome':{'name':'Goal'}}),
            event('extra','Shot',period=3,shot={'type':{'name':'Open Play'},'outcome':{'name':'Goal'}})]
        p=player_profile(es,1)
        self.assertEqual(p['actions'],6)
        self.assertEqual(p['goals'],2)
        self.assertEqual(p['counts'],dict(non_penalty_shots=1,completed_takeons=1,shot_assists=1,passes_into_box=1,forward_passes=1))
        self.assertFalse(player_profile(es,999)['appearance'])

    def test_invalid_evidence_fails_and_pooled_rates_use_exposure_weighting(self):
        shot=event('s','Shot',shot={'type':{'name':'Open Play'},'outcome':{'name':'Off T'}})
        with self.assertRaises(ValueError):player_profile([shot,deepcopy(shot)],1)
        bad=event('p','Pass',location=[1,1],**{'pass':{'end_location':[2,2],'assisted_shot_id':'missing'}})
        with self.assertRaises(ValueError):player_profile([bad],1)
        a=player_profile([shot],1)
        b=player_profile([event(str(i),'Pass',location=[1,1],**{'pass':{'end_location':[2,2]}}) for i in range(9)],1)
        pooled=pooled_profile([a,b])
        self.assertEqual(pooled['rates']['non_penalty_shots'],10)  # Not mean(100, 0) = 50.
        self.assertTrue(all(v is None for v in pooled_profile([])['rates'].values()))

    def test_snapshot_reconciles_and_henry_match_cannot_be_in_its_own_baseline(self):
        s=load_study();r=s['reference']
        self.assertEqual((r['appearances'],r['goals'],len(s['source_sha256'])),(37,30,39))
        self.assertEqual(s['score_discrepancies'],[])
        self.assertTrue(any(c['status']=='UNVERIFIED' for c in s['checks']))
        target=next(t for t in s['targets'].values() if t['player']=='Thierry Henry')
        h=s['reference_without_liverpool']
        self.assertEqual(h['appearances'],36)
        self.assertEqual(r['actions']-target['actions'],h['actions'])
        for k in METRICS:
            self.assertEqual(r['counts'][k]-target['counts'][k],h['counts'][k])
            self.assertAlmostEqual(h['rates'][k],100*h['counts'][k]/h['actions'])
        ET.fromstring(comparison_wheel(target,h))

    def test_career_colour_shares_are_appearance_based_and_reconcile(self):
        for name,r in CAREERS.items():
            self.assertAlmostEqual(sum(x[2] for x in club_shares(name)),1)
            self.assertEqual(sum(x[1] for x in club_shares(name)),r['appearances'])
            self.assertIn('not playing minutes',career_html(name))
        self.assertEqual(len(club_shares('Lampard-inspired')),3)
        self.assertEqual(club_shares('Fabregas-inspired')[0][0],'Arsenal')
        self.assertEqual(career_html('Unknown-inspired'),'')

    def test_card_background_uses_exact_appearance_shares_and_safe_fallback(self):
        from pl_dna.historical import sourced_season_card
        bg = club_background('Lampard-inspired')
        self.assertIn('#2463eb 0.000000% 70.443350%', bg)
        self.assertIn('#7a263a 70.443350% 94.745484%', bg)
        self.assertIn('#6cabdd 94.745484% 100.000000%', bg)
        self.assertIsNone(club_background('Unknown-inspired'))
        for legend in CAREERS:
            card = sourced_season_card(legend)
            self.assertIn(club_background(legend), card)
            self.assertIn('Selected season · separate from career totals', card)
            self.assertIn('PREMIER LEAGUE CAREER', card)
        # Career data is never silently extrapolated to unverified legends.
        self.assertNotIn('SOURCE SNAPSHOT', sourced_season_card('Unknown-inspired'))

    def test_all_25_legends_have_sourced_club_cards_and_scope_boundaries(self):
        from pl_dna.presentation import LEGEND_CLUBS
        self.assertEqual(set(CAREERS), set(LEGEND_CLUBS))
        self.assertEqual(dict(CAREERS['Shearer-inspired']['clubs']), {'Newcastle United':303, 'Blackburn Rovers':138})
        self.assertEqual(dict(CAREERS['Rooney-inspired']['clubs']), {'Manchester United':393, 'Everton':98})
        walker = dict(CAREERS['Kyle Walker-inspired']['clubs'])
        self.assertEqual(walker['Tottenham Hotspur'],183)
        self.assertEqual(walker['Burnley'],36)
        self.assertNotIn('Queens Park Rangers',walker)
        self.assertNotIn('Sheffield United',walker)
        self.assertEqual(CAREERS['Van Dijk-inspired']['appearances'],339)
        self.assertIn('through 2025/26',career_html('Van Dijk-inspired'))
        self.assertIn('—',career_html('Alisson-inspired'))
        self.assertNotIn('0</strong><span>PL clean sheets',career_html('Alisson-inspired'))

    def test_optional_study_and_career_card_render_without_network_or_model_calls(self):
        import test_dashboard
        with patch('pl_dna.microsoft_provider.create_provider_from_env',new=Mock()) as provider:
            at=test_dashboard.DashboardTests().app()
            self.assertIn('177</strong>',test_dashboard.html(at))
            self.assertIn('West Ham United',test_dashboard.html(at))
            at.radio(key='data_source').set_value('Recorded midfield comparison').run()
            self.assertEqual(list(at.exception), [])
            self.assertTrue(any('Estimated blend' in m.value for m in at.markdown))
            self.assertEqual(sum(int(m.value.rstrip('%')) for m in at.metric), 100)
            provider.assert_not_called()

if __name__=='__main__':unittest.main()
