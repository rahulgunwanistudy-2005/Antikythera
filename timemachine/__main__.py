import argparse
import json
from pathlib import Path
from .engine import analyze, era_ablation

parser = argparse.ArgumentParser(description='Temporal matched analysis; empty data never produces a headline.')
parser.add_argument('dataset', type=Path)
parser.add_argument('--freeze', type=int, default=2000)
parser.add_argument('--follow-up', type=int, default=20)
parser.add_argument('--seed', type=int, default=42)
parser.add_argument('--bootstrap', type=int, default=300)
parser.add_argument('--imputations', type=int, default=20)
parser.add_argument('--ablation', action='store_true')
parser.add_argument('--output', type=Path)
args = parser.parse_args()
data = json.loads(args.dataset.read_text())
fn = era_ablation if args.ablation else analyze
result = fn(data, freeze_year=args.freeze, follow_up=args.follow_up, seed=args.seed,
            bootstrap=args.bootstrap, imputations=args.imputations)
rendered = json.dumps(result, indent=2, allow_nan=False) + '\n'
if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered)
else:
    print(rendered, end='')
