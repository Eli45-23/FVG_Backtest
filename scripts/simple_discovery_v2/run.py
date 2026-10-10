"""Additive adapter over the preserved v1 account/native-execution runner."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.simple_discovery import run as base
from scripts.simple_discovery_v2.core import Detector,HYPOTHESES
P=ROOT/'work/simple-strategy-discovery-v2'

def main():
    base.P=P
    base.Detector=Detector
    base.HYPOTHESES=HYPOTHESES
    base.main()

if __name__=='__main__': main()
