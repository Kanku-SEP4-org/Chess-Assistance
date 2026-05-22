"""
Fetch chess games from Lichess across diverse ELO brackets to reduce
single-player bias in the angriness predictor training dataset.

Produces a CSV with the same columns as angriness_dataset.csv but with
games from ~150 players spanning 800-3000+ ELO.

Usage:
    python fetch_diverse_elo_games.py
    python fetch_diverse_elo_games.py --skip-kaggle   # use only Lichess leaderboard
    python fetch_diverse_elo_games.py --dry-run        # show player selection without fetching
"""

import argparse
import json
import math
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_CSV = DATA_DIR / "raw" / "angriness_dataset_diverse.csv"
EXISTING_CSV = DATA_DIR / "legacy" / "angriness_dataset.csv"

GAMES_PER_PLAYER = 200
PLAYERS_PER_BRACKET = 30
RATE_LIMIT_SLEEP = 1.5
SEED = 42

BRACKETS = {
    "beginner": (800, 1200),
    "intermediate": (1200, 1600),
    "advanced": (1600, 2000),
    "expert": (2000, 2400),
    "master": (2400, 4000),
}

CSV_COLUMNS = [
    "sleep_duration",
    "consecutive_losses",
    "awaken_duration",
    "avg_tpm",
    "move_cnt",
    "inaccuracy_cnt_player",
    "mistake_cnt_player",
    "blunder_cnt_player",
    "elo",
    "elo_diff",
    "game_id",
    "username",
    "created_at",
    "last_move_at",
    "player_color",
    "time_control_initial",
    "time_control_increment",
    "opponent_elo",
    "elo_gap",
    "move_cnt_player",
    "avg_tpm_seconds_player",
    "consecutive_losses_pregame",
    "acpl_player",
    "accuracy_player",
    "avg_ppm",
    "avg_celsius",
    "water_intake_ml",
    "avg_lux",
]

LICHESS_BASE = "https://lichess.org"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rate_limited_get(url: str, params: dict | None = None,
                      headers: dict | None = None, max_retries: int = 5) -> requests.Response | None:
    hdrs = {"Accept": "application/x-ndjson"}
    if headers:
        hdrs.update(headers)

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, headers=hdrs, timeout=60)
        except requests.RequestException as exc:
            print(f"  [!] Request error: {exc}")
            time.sleep(RATE_LIMIT_SLEEP * attempt)
            continue

        if resp.status_code == 429:
            wait = 60 * attempt
            print(f"  [!] Rate limited — waiting {wait}s (attempt {attempt}/{max_retries})")
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            print(f"  [!] HTTP {resp.status_code} for {url}")
            return None

        time.sleep(RATE_LIMIT_SLEEP)
        return resp

    print(f"  [!] Max retries exceeded for {url}")
    return None


def _rate_limited_post(url: str, data: str,
                       headers: dict | None = None, max_retries: int = 5) -> requests.Response | None:
    hdrs = {"Accept": "application/json", "Content-Type": "text/plain"}
    if headers:
        hdrs.update(headers)

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, data=data, headers=hdrs, timeout=60)
        except requests.RequestException as exc:
            print(f"  [!] Request error: {exc}")
            time.sleep(RATE_LIMIT_SLEEP * attempt)
            continue

        if resp.status_code == 429:
            wait = 60 * attempt
            print(f"  [!] Rate limited — waiting {wait}s (attempt {attempt}/{max_retries})")
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            print(f"  [!] HTTP {resp.status_code} for {url}")
            return None

        time.sleep(RATE_LIMIT_SLEEP)
        return resp

    print(f"  [!] Max retries exceeded for {url}")
    return None


def _load_cache(name: str) -> dict | list | None:
    path = CACHE_DIR / f"{name}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def _save_cache(name: str, data):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / f"{name}.json", "w") as f:
        json.dump(data, f)


# ---------------------------------------------------------------------------
# Phase 1: Collect usernames by ELO bracket
# ---------------------------------------------------------------------------

def _fetch_lichess_leaderboard_users() -> dict[str, int]:
    """Fetch top players from Lichess leaderboards (blitz + bullet + rapid)."""
    cached = _load_cache("leaderboard_users")
    if cached:
        print(f"  Loaded {len(cached)} leaderboard users from cache")
        return cached

    users: dict[str, int] = {}
    for perf in ["blitz", "bullet", "rapid"]:
        url = f"{LICHESS_BASE}/api/player/top/200/{perf}"
        resp = _rate_limited_get(url, headers={"Accept": "application/vnd.lichess.v3+json"})
        if resp is None:
            continue
        data = resp.json()
        for u in data.get("users", []):
            uid = u.get("id", "").lower()
            rating = u.get("perfs", {}).get(perf, {}).get("rating")
            if uid and rating:
                users[uid] = max(users.get(uid, 0), rating)
        print(f"  Fetched {perf} leaderboard: {len(data.get('users', []))} players")

    _save_cache("leaderboard_users", users)
    print(f"  Total leaderboard users: {len(users)}")
    return users


def _fetch_tournament_users() -> dict[str, int]:
    """Discover players across all rating levels from recent Lichess arena tournaments."""
    cached = _load_cache("tournament_users")
    if cached:
        print(f"  Loaded {len(cached)} tournament users from cache")
        return cached

    users: dict[str, int] = {}

    # Fetch recently finished arena tournaments
    resp = _rate_limited_get(
        f"{LICHESS_BASE}/api/tournament",
        headers={"Accept": "application/json"},
    )
    if resp is None:
        print("  [!] Could not fetch tournament list")
        return users

    tournaments = resp.json()
    finished = tournaments.get("finished", [])[:20]
    print(f"  Scanning {len(finished)} recent tournaments for players...")

    for tourney in finished:
        tid = tourney.get("id", "")
        resp = _rate_limited_get(
            f"{LICHESS_BASE}/api/tournament/{tid}/results",
            params={"nb": 200},
            headers={"Accept": "application/x-ndjson"},
        )
        if resp is None:
            continue

        for line in resp.text.strip().split("\n"):
            if not line:
                continue
            try:
                entry = json.loads(line)
                uid = entry.get("username", "").lower()
                rating = entry.get("rating")
                if uid and rating:
                    users[uid] = max(users.get(uid, 0), rating)
            except json.JSONDecodeError:
                pass

        print(f"    Tournament {tid}: pool now {len(users)} users")

    _save_cache("tournament_users", users)
    print(f"  Total tournament users: {len(users)}")
    return users


def _fetch_kaggle_users() -> dict[str, int]:
    """Use the Kaggle Lichess dataset to get usernames with known ratings."""
    cached = _load_cache("kaggle_users")
    if cached:
        print(f"  Loaded {len(cached)} Kaggle users from cache")
        return cached

    try:
        import kagglehub
        path = kagglehub.dataset_download("ahmedalghafri/lichess-chess-games-statistics")
        csv_path = os.path.join(path, "Chess games stats.csv")
        df = pd.read_csv(csv_path)
    except Exception as exc:
        print(f"  [!] Could not load Kaggle dataset: {exc}")
        print("  [!] Falling back to Lichess leaderboard only")
        return {}

    game_ids = df["Game ID"].tolist()
    users: dict[str, int] = {}

    print(f"  Fetching usernames for {len(game_ids)} Kaggle games...")
    for i in range(0, len(game_ids), 300):
        batch = game_ids[i : i + 300]
        resp = _rate_limited_post(
            f"{LICHESS_BASE}/games/export/_ids",
            data=",".join(str(gid) for gid in batch),
            headers={"Accept": "application/x-ndjson"},
        )
        if resp is None:
            continue

        for line in resp.text.strip().split("\n"):
            if not line:
                continue
            try:
                game = json.loads(line)
                for side in ("white", "black"):
                    player = game.get("players", {}).get(side, {})
                    uid = player.get("user", {}).get("id", "").lower()
                    rating = player.get("rating")
                    if uid and rating:
                        users[uid] = max(users.get(uid, 0), rating)
            except json.JSONDecodeError:
                pass

        if (i // 300) % 20 == 0:
            print(f"    Processed {min(i + 300, len(game_ids))}/{len(game_ids)} games ({len(users)} users)")

    _save_cache("kaggle_users", users)
    print(f"  Total Kaggle users: {len(users)}")
    return users


def _batch_fetch_user_ratings(usernames: list[str]) -> dict[str, dict]:
    """Fetch blitz/rapid/bullet ratings for a list of usernames via POST /api/users."""
    cache_name = "user_ratings_batch"
    cached = _load_cache(cache_name)
    if cached:
        print(f"  Loaded {len(cached)} user ratings from cache")
        return cached

    ratings: dict[str, dict] = {}

    for i in range(0, len(usernames), 300):
        batch = usernames[i : i + 300]
        resp = _rate_limited_post(
            f"{LICHESS_BASE}/api/users",
            data=",".join(batch),
        )
        if resp is None:
            continue

        for user in resp.json():
            uid = user.get("id", "").lower()
            perfs = user.get("perfs", {})
            ratings[uid] = {
                "blitz": perfs.get("blitz", {}).get("rating"),
                "rapid": perfs.get("rapid", {}).get("rating"),
                "bullet": perfs.get("bullet", {}).get("rating"),
                "blitz_games": perfs.get("blitz", {}).get("games", 0),
                "rapid_games": perfs.get("rapid", {}).get("games", 0),
                "bullet_games": perfs.get("bullet", {}).get("games", 0),
            }

        print(f"    Fetched ratings for {min(i + 300, len(usernames))}/{len(usernames)}")

    _save_cache(cache_name, ratings)
    return ratings


def select_players(skip_kaggle: bool = False) -> dict[str, list[str]]:
    """Select PLAYERS_PER_BRACKET usernames for each ELO bracket."""
    rng = np.random.default_rng(SEED)

    print("\n=== Phase 1: Collecting usernames ===")

    all_users: dict[str, int] = {}
    leaderboard = _fetch_lichess_leaderboard_users()
    all_users.update(leaderboard)

    tournament = _fetch_tournament_users()
    all_users.update(tournament)

    if not skip_kaggle:
        kaggle = _fetch_kaggle_users()
        all_users.update(kaggle)

    print(f"\n  Combined pool: {len(all_users)} unique users")

    # Fetch proper blitz ratings for all users
    all_usernames = list(all_users.keys())
    detailed_ratings = _batch_fetch_user_ratings(all_usernames)

    # Use blitz rating as canonical bracket assignment
    user_blitz: dict[str, int] = {}
    for uid, ratings in detailed_ratings.items():
        blitz = ratings.get("blitz")
        if blitz and ratings.get("blitz_games", 0) >= 10:
            user_blitz[uid] = blitz

    print(f"  Users with valid blitz rating (10+ games): {len(user_blitz)}")

    selected: dict[str, list[str]] = {}
    for bracket_name, (lo, hi) in BRACKETS.items():
        candidates = [uid for uid, r in user_blitz.items() if lo <= r < hi]
        n = min(PLAYERS_PER_BRACKET, len(candidates))
        if n == 0:
            print(f"  [!] No candidates for {bracket_name} ({lo}-{hi})")
            selected[bracket_name] = []
            continue
        chosen = rng.choice(candidates, size=n, replace=False).tolist()
        selected[bracket_name] = chosen
        print(f"  {bracket_name} ({lo}-{hi}): {n} players selected from {len(candidates)} candidates")

    return selected


# ---------------------------------------------------------------------------
# Phase 2: Fetch games per player
# ---------------------------------------------------------------------------

def fetch_player_games(username: str) -> list[dict]:
    """Fetch up to GAMES_PER_PLAYER analyzed games for a player."""
    cache_name = f"games_{username}"
    cached = _load_cache(cache_name)
    if cached is not None:
        return cached

    resp = _rate_limited_get(
        f"{LICHESS_BASE}/api/games/user/{username}",
        params={
            "max": GAMES_PER_PLAYER,
            "sort": "dateDesc",
            "opening": "true",
            "evals": "true",
            "clocks": "true",
            "moves": "true",
            "pgnInJson": "true",
        },
    )

    if resp is None:
        _save_cache(cache_name, [])
        return []

    games = []
    for line in resp.text.strip().split("\n"):
        if not line:
            continue
        try:
            game = json.loads(line)
            games.append(game)
        except json.JSONDecodeError:
            pass

    _save_cache(cache_name, games)
    return games


# ---------------------------------------------------------------------------
# Phase 3: Extract CSV rows
# ---------------------------------------------------------------------------

def _determine_player_side(game: dict, username: str) -> str | None:
    """Return 'white' or 'black' based on which side the player is."""
    white_id = game.get("players", {}).get("white", {}).get("user", {}).get("id", "").lower()
    black_id = game.get("players", {}).get("black", {}).get("user", {}).get("id", "").lower()
    uname = username.lower()
    if white_id == uname:
        return "white"
    if black_id == uname:
        return "black"
    return None


def extract_csv_rows(games: list[dict], username: str, rng: np.random.Generator) -> list[dict]:
    """Convert a list of Lichess game JSONs into CSV rows for the angriness dataset."""
    rows = []

    sorted_games = sorted(games, key=lambda g: g.get("createdAt", 0))

    for idx, game in enumerate(sorted_games):
        side = _determine_player_side(game, username)
        if side is None:
            continue

        other_side = "black" if side == "white" else "white"
        player = game.get("players", {}).get(side, {})
        opponent = game.get("players", {}).get(other_side, {})

        analysis = player.get("analysis")
        if analysis is None:
            continue

        inaccuracy = analysis.get("inaccuracy")
        mistake = analysis.get("mistake")
        blunder = analysis.get("blunder")
        acpl = analysis.get("acpl")
        accuracy = analysis.get("accuracy")

        if acpl is None:
            continue

        moves_str = game.get("moves", "")
        if not moves_str:
            continue

        total_ply = len(moves_str.split())
        is_black = side == "black"
        player_move_count = total_ply // 2 if is_black else (total_ply + 1) // 2

        if player_move_count == 0:
            continue

        created_at = game.get("createdAt", 0)
        last_move_at = game.get("lastMoveAt", 0)
        duration_seconds = (last_move_at - created_at) / 1000.0

        if duration_seconds <= 0:
            continue

        avg_tpm = duration_seconds / total_ply if total_ply > 0 else None
        avg_tpm_player = duration_seconds / player_move_count

        elo = player.get("rating", 0)
        elo_diff = player.get("ratingDiff", 0)
        opponent_elo = opponent.get("rating", 0)
        elo_gap = elo - opponent_elo

        winner = game.get("winner")
        if winner is None:
            is_loss = False
        elif winner == side:
            is_loss = False
        else:
            is_loss = True

        consecutive_losses = 0
        for prev_idx in range(idx - 1, -1, -1):
            prev_game = sorted_games[prev_idx]
            prev_side = _determine_player_side(prev_game, username)
            if prev_side is None:
                break
            prev_winner = prev_game.get("winner")
            if prev_winner is not None and prev_winner != prev_side:
                consecutive_losses += 1
            else:
                break

        clock = game.get("clock", {})
        tc_initial = clock.get("initial", 0) if clock else 0
        tc_increment = clock.get("increment", 0) if clock else 0

        sleep_duration = float(np.clip(rng.normal(7.0, 1.5), 3.0, 12.0))
        awaken_duration = float(np.clip(rng.normal(4.0, 2.0), 0.5, 16.0))

        rows.append({
            "sleep_duration": round(sleep_duration, 2),
            "consecutive_losses": consecutive_losses,
            "awaken_duration": round(awaken_duration, 2) if awaken_duration else "",
            "avg_tpm": avg_tpm,
            "move_cnt": total_ply,
            "inaccuracy_cnt_player": inaccuracy,
            "mistake_cnt_player": mistake,
            "blunder_cnt_player": blunder,
            "elo": elo,
            "elo_diff": elo_diff,
            "game_id": game.get("id", ""),
            "username": username,
            "created_at": created_at,
            "last_move_at": last_move_at,
            "player_color": side,
            "time_control_initial": tc_initial,
            "time_control_increment": tc_increment,
            "opponent_elo": opponent_elo,
            "elo_gap": elo_gap,
            "move_cnt_player": player_move_count,
            "avg_tpm_seconds_player": avg_tpm_player,
            "consecutive_losses_pregame": consecutive_losses,
            "acpl_player": acpl,
            "accuracy_player": accuracy,
            "avg_ppm": round(float(np.clip(rng.normal(1549, 326.60), 1179, 2393)), 2),
            "avg_celsius": round(float(np.clip(rng.normal(25.17, 2.12), 22.10, 28.75)), 2),
            "water_intake_ml": int(np.clip(rng.normal(700, 300), 300, 1500)),
            "avg_lux": round(float(np.clip(rng.normal(400, 200), 50, 1000)), 2),
        })

    return rows


# ---------------------------------------------------------------------------
# Phase 4: Merge & balance
# ---------------------------------------------------------------------------

def merge_and_balance(new_df: pd.DataFrame, downsample_magnus: int = 6000) -> pd.DataFrame:
    """Merge new diverse data with existing CSV, optionally downsample Magnus."""
    if EXISTING_CSV.exists():
        existing = pd.read_csv(EXISTING_CSV)
        print(f"\n  Existing CSV: {len(existing)} rows (all {existing['username'].nunique()} player(s))")

        if downsample_magnus > 0:
            magnus_mask = existing["username"] == "DrNykterstein"
            magnus_rows = existing[magnus_mask]
            other_rows = existing[~magnus_mask]

            if len(magnus_rows) > downsample_magnus:
                magnus_sampled = magnus_rows.sample(n=downsample_magnus, random_state=SEED)
                existing = pd.concat([magnus_sampled, other_rows], ignore_index=True)
                print(f"  Downsampled DrNykterstein: {len(magnus_rows)} → {downsample_magnus}")
    else:
        existing = pd.DataFrame(columns=CSV_COLUMNS)

    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["game_id", "username"], keep="first")

    return combined


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch diverse ELO games for angriness predictor")
    parser.add_argument("--skip-kaggle", action="store_true",
                        help="Skip Kaggle dataset, use Lichess leaderboard only")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show player selection without fetching games")
    parser.add_argument("--no-downsample", action="store_true",
                        help="Keep all existing Magnus rows instead of downsampling")
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    selected = select_players(skip_kaggle=args.skip_kaggle)

    total_players = sum(len(v) for v in selected.values())
    print(f"\n  Total selected: {total_players} players across {len(selected)} brackets")

    if args.dry_run:
        for bracket, players in selected.items():
            print(f"\n  {bracket}: {players[:5]}{'...' if len(players) > 5 else ''}")
        print("\n  Dry run — no games fetched.")
        return

    # Phase 2 & 3: Fetch and extract
    rng = np.random.default_rng(SEED)
    all_rows: list[dict] = []

    for bracket, players in selected.items():
        print(f"\n=== Phase 2-3: Fetching {bracket} ({len(players)} players) ===")
        bracket_rows = 0
        for i, username in enumerate(players):
            games = fetch_player_games(username)
            rows = extract_csv_rows(games, username, rng)
            all_rows.extend(rows)
            bracket_rows += len(rows)
            print(f"  [{i+1}/{len(players)}] {username}: {len(games)} games → {len(rows)} valid rows")
        print(f"  {bracket} total: {bracket_rows} rows")

    new_df = pd.DataFrame(all_rows, columns=CSV_COLUMNS)
    print(f"\n=== Phase 4: Merge & balance ===")
    print(f"  New rows: {len(new_df)}")

    downsample = 0 if args.no_downsample else 6000
    final_df = merge_and_balance(new_df, downsample_magnus=downsample)

    final_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  Output: {OUTPUT_CSV}")
    print(f"  Total rows: {len(final_df)}")
    print(f"  Unique players: {final_df['username'].nunique()}")

    # Summary by ELO bracket
    bins = [0, 1200, 1600, 2000, 2400, 5000]
    labels = ["800-1200", "1200-1600", "1600-2000", "2000-2400", "2400+"]
    final_df["_bracket"] = pd.cut(final_df["elo"], bins=bins, labels=labels)
    print("\n  Rows per ELO bracket:")
    print(final_df["_bracket"].value_counts().sort_index().to_string())

    print("\n  ACPL by bracket (median):")
    print(final_df.groupby("_bracket", observed=True)["acpl_player"].median().to_string())

    print("\nDone.")


if __name__ == "__main__":
    main()
