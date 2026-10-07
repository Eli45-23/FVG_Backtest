"""Single compatibility boundary for the preserved reference implementation."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'outputs'))
import cont_a_backtest as reference
import cont_a_metrics as metrics
