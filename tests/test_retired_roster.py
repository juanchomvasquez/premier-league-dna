from copy import deepcopy
import unittest
from pl_dna.retired_roster import REPLACEMENTS,records
from pl_dna.career import CAREERS,club_shares
from pl_dna.historical import SEASON_FACTS,sourced_season_card
from pl_dna.presentation import LEGEND_CLUBS
from pl_dna.roles import ROLE_DEFINITIONS
from pl_dna.current_dashboard import load_current,wheel
from pl_dna.season_comparison import compare_season_player
from pl_dna.analyst_brief import generate_analyst_brief

class RetiredRosterTests(unittest.TestCase):
 def test_all_public_catalogues_use_approved_retired_roster(self):
  expected=set(LEGEND_CLUBS)
  self.assertEqual(len(expected),25)
  self.assertEqual(set(CAREERS),expected);self.assertEqual(set(SEASON_FACTS),expected)
  self.assertFalse(set(REPLACEMENTS)&expected)
  self.assertTrue(set(REPLACEMENTS.values())<=expected)
  inspirations={n for r in ROLE_DEFINITIONS.values() for n in r['legend_inspirations'].values()}
  self.assertEqual(inspirations,expected)
  for name in expected:self.assertAlmostEqual(sum(s[2] for s in club_shares(name)),1)
  self.assertIn('Rio Ferdinand-inspired',expected)
  self.assertNotIn('Carvalho-inspired',expected)

 def test_missing_earlier_seasons_are_not_replaced_with_zeros(self):
  for name in ['Vieira-inspired','Bergkamp-inspired']:
   self.assertIsNone(records()[name]['season']['appearances'])
   self.assertIn('—',sourced_season_card(name))
  study=load_current()
  self.assertFalse(set(REPLACEMENTS)&{r['inspiration'] for r in study['references']})
  self.assertTrue({'Dennis Bergkamp'}<={r['player'] for r in study['unavailable_references']})
  self.assertTrue(any(e['player']['name']=='Virgil van Dijk' for e in study['targets'].values()))

 def test_cdm_references_use_real_samples_with_exact_scope(self):
  study=load_current();refs=[r for r in study['references'] if r['role']=='CDM']
  self.assertEqual({r['player'] for r in refs},{'Roy Keane','Patrick Vieira','Claude Makelele'})
  self.assertEqual(sorted(len(r['matches']) for r in refs),[2,2,3])
  self.assertTrue(all(r['reference_kind']=='match_sample' for r in refs))
  self.assertTrue(all(r['counts']['long_passes'] is None for r in refs))
  self.assertNotIn('Carrick-inspired',CAREERS)
  self.assertEqual(dict(CAREERS['Keane-inspired']['clubs']),{'Manchester United':326,'Nottingham Forest':40})
  e=next(e for e in study['targets'].values() if e['role']=='CDM')
  p=compare_season_player(e['player'],e['snapshot'],e['fixture'],refs,'CDM')
  self.assertFalse(p['availability']);self.assertEqual(p['reference_kind'],'match_sample')
  self.assertEqual(set(p['metric_keys']),{'passes','tackles','interceptions','recoveries'})
  self.assertEqual(sum(p['fit']['percentages'].values()),100)

 def test_cdm_can_keep_match_facts_wheel_and_ai_without_forced_blend(self):
  study=load_current();e=next(e for e in study['targets'].values() if e['role']=='CDM')
  p=compare_season_player(e['player'],e['snapshot'],e['fixture'],[r for r in study['references'] if r['player']=='Roy Keane'],'CDM')
  self.assertEqual(p['fit_status'],'comparison_unavailable');self.assertNotIn('fit',p)
  self.assertTrue(p['interpretation_available']);self.assertIn('counts per 90',wheel(p))
  self.assertNotIn('#b69aff',wheel(p))
  reply={'headline':'Recorded contributions without a historical blend',
   'narrative':'The available measurements describe involvement through passing and defensive actions. They remain useful observations, but the limited historical reference coverage prevents a supported legend blend and does not establish an overall performance grade.',
   'evidence_ids':[p['evidence'][0]['id'],p['evidence'][1]['id']]}
  result=generate_analyst_brief(p,lambda _:reply)
  self.assertEqual(result['status'],'evidence_checked')
