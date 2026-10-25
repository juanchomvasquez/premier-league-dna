"""Approved retired-only roster; historical facts stay distinct from demo values."""
import json
from pathlib import Path

REPLACEMENTS={
 'Alisson-inspired':'Van der Sar-inspired',
 'Van Dijk-inspired':'Rio Ferdinand-inspired',
 'Kyle Walker-inspired':'Gary Neville-inspired',
 'Alexander-Arnold-inspired':'Baines-inspired',
 'Kante-inspired':'Vieira-inspired',
 'Rodri-inspired':'Keane-inspired',
 'De Bruyne-inspired':'Bergkamp-inspired',
 'Ronaldo-inspired':'Giggs-inspired',
 'Salah-inspired':'Bale-inspired',
}

def records():
    return json.loads((Path(__file__).parent/'data/retired_roster.json').read_text())

def apply_roster(mapping,field):
    for old in REPLACEMENTS:mapping.pop(old,None)
    mapping.update({name:r[field] for name,r in records().items()})
