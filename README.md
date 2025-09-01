# FPL Predictor (async, formation-aware)

**What it does.** Pulls live FPL data and builds valid lineups under common formations, comparing multiple selection heuristics and captain policies (including a coefficient-of-variation captain to reduce volatility). Prints each strategy’s XI, captain choice, team cost, and points for a given Gameweek.

## Key ideas
- Asynchronous API pulls for player history and metadata.
- Strategy families:
  - `cheap_*`: value sort by (PPG^2 / cost)
  - `points_*`: sort by points_per_game
  - `pointsovertime_*`: sort by trailing-k average
  - `*_cv_team`: pick captain by low variance (CV) with outlier-trim
  - `*_salah_team`: realistic fallback captain (Salah → Haaland)
- Formation constraint builder (e.g., 1-3-5-2, 1-4-4-2).
- Console tables via PrettyTable.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/fpl_predictor.py --gw 5 --k 2 --excused 1 --strategy pointsovertime_cv
