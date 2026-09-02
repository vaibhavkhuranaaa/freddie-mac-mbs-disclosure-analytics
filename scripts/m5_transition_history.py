#!/usr/bin/env python3
"""Build bounded-memory loan transition components from M4 partitions."""

from __future__ import annotations

import csv
import gzip
import sqlite3
from collections import defaultdict
from contextlib import closing
from pathlib import Path
from typing import Any, Iterable, Mapping


HISTORY_COLUMNS = {
    "report_period", "loan_id", "security_id", "correction_indicator",
    "current_upb_cents", "days_delinquent", "modification_program",
    "join_reason", "source_family", "source_file", "source_row",
    "publication_date", "as_of_timestamp",
}
VIEWS = ("original", "latest")
DELINQUENT_STATES = {"30-59", "60-89", "90+"}

HISTORY_SCHEMA = """
PRAGMA journal_mode = OFF;
PRAGMA synchronous = OFF;
PRAGMA temp_store = FILE;
PRAGMA cache_size = -32768;
CREATE TABLE current_history (
  source_family TEXT NOT NULL,
  loan_id TEXT NOT NULL,
  security_id TEXT NOT NULL,
  original_rank TEXT NOT NULL,
  original_active INTEGER NOT NULL,
  original_upb INTEGER,
  original_days INTEGER,
  original_modified INTEGER NOT NULL,
  latest_rank TEXT NOT NULL,
  latest_active INTEGER NOT NULL,
  latest_upb INTEGER,
  latest_days INTEGER,
  latest_modified INTEGER NOT NULL,
  PRIMARY KEY (source_family, loan_id, security_id)
) WITHOUT ROWID;
CREATE TABLE prior_history AS SELECT * FROM current_history WHERE 0;
CREATE UNIQUE INDEX prior_history_key
  ON prior_history(source_family, loan_id, security_id);
CREATE TABLE cohort (
  correction_view TEXT NOT NULL,
  source_family TEXT NOT NULL,
  loan_id TEXT NOT NULL,
  security_id TEXT NOT NULL,
  start_period TEXT NOT NULL,
  trigger TEXT NOT NULL,
  start_upb INTEGER NOT NULL,
  last_period TEXT NOT NULL,
  status TEXT NOT NULL,
  PRIMARY KEY (
    correction_view, source_family, loan_id, security_id, start_period, trigger
  )
) WITHOUT ROWID;
"""

UPSERT_HISTORY = """
INSERT INTO current_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(source_family, loan_id, security_id) DO UPDATE SET
  original_active=CASE WHEN excluded.original_rank < original_rank
    THEN excluded.original_active ELSE original_active END,
  original_upb=CASE WHEN excluded.original_rank < original_rank
    THEN excluded.original_upb ELSE original_upb END,
  original_days=CASE WHEN excluded.original_rank < original_rank
    THEN excluded.original_days ELSE original_days END,
  original_modified=CASE WHEN excluded.original_rank < original_rank
    THEN excluded.original_modified ELSE original_modified END,
  original_rank=MIN(original_rank, excluded.original_rank),
  latest_active=CASE WHEN excluded.latest_rank > latest_rank
    THEN excluded.latest_active ELSE latest_active END,
  latest_upb=CASE WHEN excluded.latest_rank > latest_rank
    THEN excluded.latest_upb ELSE latest_upb END,
  latest_days=CASE WHEN excluded.latest_rank > latest_rank
    THEN excluded.latest_days ELSE latest_days END,
  latest_modified=CASE WHEN excluded.latest_rank > latest_rank
    THEN excluded.latest_modified ELSE latest_modified END,
  latest_rank=MAX(latest_rank, excluded.latest_rank)
"""


class TransitionError(ValueError):
    """Fail-closed transition history error."""


def integer(raw: str | None) -> int | None:
    if raw is None or not raw.strip():
        return None
    return int(raw)


def month_index(period: str) -> int:
    return int(period[:4]) * 12 + int(period[5:])


def adjacent_month(prior: str, current: str) -> bool:
    return month_index(current) - month_index(prior) == 1


def component(
    contract: str,
    name: str,
    period: str,
    view: str,
    dimension: str,
    member: str,
    numerator: int,
    denominator: int | None,
    observations: int,
) -> tuple[Any, ...]:
    return (
        contract, name, period, view, "loan-cohort", dimension, member,
        str(numerator), None if denominator is None else str(denominator),
        observations,
    )


def rank(row: list[str], positions: dict[str, int]) -> str:
    source_row = integer(row[positions["source_row"]]) or 0
    return "\x1f".join((
        row[positions["as_of_timestamp"]],
        row[positions["publication_date"]],
        row[positions["source_file"]],
        f"{source_row:012d}",
    ))


def history_row(row: list[str], positions: dict[str, int]) -> tuple[Any, ...]:
    upb = integer(row[positions["current_upb_cents"]])
    correction = row[positions["correction_indicator"]]
    active = int(
        row[positions["join_reason"]] == "matched"
        and correction != "D"
        and upb is not None
        and upb > 0
    )
    days = integer(row[positions["days_delinquent"]])
    modified = int(bool(row[positions["modification_program"]].strip()))
    precedence = rank(row, positions)
    identity = (
        row[positions["source_family"]], row[positions["loan_id"]],
        row[positions["security_id"]],
    )
    values = (precedence, active, upb, days, modified)
    return (*identity, *values, *values)


def stage_period(
    connection: sqlite3.Connection,
    sources: Iterable[Mapping[str, Any]],
    partition_root: Path,
    period: str,
) -> int:
    connection.execute("DELETE FROM current_history")
    scanned = 0
    batch: list[tuple[Any, ...]] = []
    for source in sorted(sources, key=lambda item: item["source_file"]):
        path = partition_root / source["partition_path"]
        with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            try:
                headers = next(reader)
            except StopIteration as error:
                raise TransitionError("loan history partition is empty") from error
            missing = HISTORY_COLUMNS - set(headers)
            if missing:
                raise TransitionError("loan history partition omits required columns")
            positions = {name: headers.index(name) for name in HISTORY_COLUMNS}
            for row in reader:
                scanned += 1
                if len(row) != len(headers):
                    raise TransitionError("loan history partition row width changed")
                if row[positions["report_period"]] != period:
                    raise TransitionError("loan history partition period changed")
                batch.append(history_row(row, positions))
                if len(batch) == 10_000:
                    connection.executemany(UPSERT_HISTORY, batch)
                    batch.clear()
    if batch:
        connection.executemany(UPSERT_HISTORY, batch)
    expected = sum(item["partition_row_count"] for item in sources)
    if scanned != expected:
        raise TransitionError("loan history partition rows do not reconcile")
    return scanned


def transition_groups(
    connection: sqlite3.Connection,
    view: str,
) -> list[tuple[str, str, int, int]]:
    active = f"{view}_active"
    upb = f"{view}_upb"
    days = f"{view}_days"
    destination = f"""
      CASE WHEN c.source_family IS NULL OR c.{active}=0 OR c.{days} IS NULL
        THEN 'Attrition'
        WHEN c.{days} <= 0 THEN 'Current'
        WHEN c.{days} < 30 THEN '1-29'
        WHEN c.{days} < 60 THEN '30-59'
        WHEN c.{days} < 90 THEN '60-89'
        ELSE '90+' END
    """
    return list(connection.execute(
        f"""
        SELECT CASE WHEN p.{days} <= 0 THEN 'Current'
                    WHEN p.{days} < 30 THEN '1-29'
                    WHEN p.{days} < 60 THEN '30-59'
                    WHEN p.{days} < 90 THEN '60-89'
                    ELSE '90+' END AS origin,
               {destination} AS destination,
               COUNT(*), SUM(p.{upb})
        FROM prior_history p
        LEFT JOIN current_history c USING(source_family, loan_id, security_id)
        WHERE p.{active}=1 AND p.{days} IS NOT NULL
        GROUP BY origin, destination
        """
    ))


def advance_cohorts(
    connection: sqlite3.Connection,
    prior_period: str,
    period: str,
    threshold: int,
    window: int,
) -> None:
    if not adjacent_month(prior_period, period):
        connection.execute("UPDATE cohort SET status='censored' WHERE status='open'")
        return
    for view in VIEWS:
        active, days = f"{view}_active", f"{view}_days"
        identity = """
          c.source_family=h.source_family AND c.loan_id=h.loan_id
          AND c.security_id=h.security_id
        """
        eligible = f"EXISTS (SELECT 1 FROM current_history c WHERE {identity} AND c.{active}=1 AND c.{days} IS NOT NULL)"
        distressed = f"EXISTS (SELECT 1 FROM current_history c WHERE {identity} AND c.{active}=1 AND c.{days}>={threshold})"
        params = (period, view, prior_period)
        connection.execute(
            f"UPDATE cohort AS h SET status='redefault', last_period=? WHERE correction_view=? AND status='open' AND last_period=? AND {distressed}",
            params,
        )
        connection.execute(
            f"UPDATE cohort AS h SET status='censored' WHERE correction_view=? AND status='open' AND last_period=? AND NOT ({eligible})",
            (view, prior_period),
        )
        connection.execute(
            f"""
            UPDATE cohort AS h SET status='complete', last_period=?
            WHERE correction_view=? AND status='open' AND last_period=?
              AND month_index(?) - month_index(start_period) >= ? AND {eligible}
            """,
            (period, view, prior_period, period, window),
        )
        connection.execute(
            f"UPDATE cohort AS h SET last_period=? WHERE correction_view=? AND status='open' AND last_period=? AND {eligible}",
            params,
        )


def insert_triggers(
    connection: sqlite3.Connection,
    period: str,
    threshold: int,
) -> None:
    for view in VIEWS:
        active, upb = f"{view}_active", f"{view}_upb"
        days, modified = f"{view}_days", f"{view}_modified"
        base = """
          SELECT ?, p.source_family, p.loan_id, p.security_id, ?, ?, c.{upb}, ?, 'open'
          FROM prior_history p JOIN current_history c
            USING(source_family, loan_id, security_id)
          WHERE p.{active}=1 AND c.{active}=1
        """
        connection.execute(
            "INSERT OR IGNORE INTO cohort " + base.format(active=active, upb=upb) +
            f" AND p.{days}>={threshold} AND c.{days}=0",
            (view, period, "cure", period),
        )
        connection.execute(
            "INSERT OR IGNORE INTO cohort " + base.format(active=active, upb=upb) +
            f" AND p.{modified}=0 AND c.{modified}=1",
            (view, period, "modification", period),
        )


def add_interval_components(
    components: dict[tuple[Any, ...], tuple[int, int | None, int]],
    connection: sqlite3.Connection,
    period: str,
    view: str,
) -> None:
    groups = transition_groups(connection, view)
    denominators: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for origin, _, count, upb in groups:
        denominators[origin][0] += count
        denominators[origin][1] += upb
    eligible_count = sum(value[0] for value in denominators.values())
    key = ("delinquency_roll_cure", "eligible_origin_count", period, view,
           "loan-cohort", "portfolio", "All")
    components[key] = (eligible_count, None, eligible_count)
    for origin, destination, count, upb in groups:
        member = f"{origin} to {destination}"
        for name, numerator, denominator in (
            ("transition_count", count, denominators[origin][0]),
            ("transition_upb", upb, denominators[origin][1]),
        ):
            key = ("delinquency_roll_cure", name, period, view,
                   "loan-cohort", "delinquency_transition", member)
            components[key] = (numerator, denominator, count)
    current_count, current_upb = denominators.get("Current", [0, 0])
    new_count = sum(
        count for origin, destination, count, _ in groups
        if origin == "Current" and destination in DELINQUENT_STATES
    )
    new_upb = sum(
        upb for origin, destination, _, upb in groups
        if origin == "Current" and destination in DELINQUENT_STATES
    )
    for name, numerator, denominator in (
        ("new_delinquency_count", new_count, current_count),
        ("new_delinquency_upb", new_upb, current_upb),
    ):
        key = ("new_delinquency_redefault", name, period, view,
               "loan-cohort", "delinquency_transition", "Current to 30+")
        components[key] = (numerator, denominator, current_count)


def cohort_component_rows(
    connection: sqlite3.Connection,
    periods: Iterable[str],
) -> list[tuple[Any, ...]]:
    totals: dict[tuple[str, str, str], dict[str, tuple[int, int]]] = defaultdict(dict)
    for period, view, trigger, status, count, upb in connection.execute(
        """
        SELECT start_period, correction_view, trigger, status, COUNT(*), SUM(start_upb)
        FROM cohort GROUP BY start_period, correction_view, trigger, status
        """
    ):
        totals[(period, view, trigger)][status] = (count, upb)
    rows: list[tuple[Any, ...]] = []
    for period in periods:
        for view in VIEWS:
            for trigger in ("cure", "modification"):
                values = totals[(period, view, trigger)]
                redefault = values.get("redefault", (0, 0))
                complete = values.get("complete", (0, 0))
                censored = tuple(
                    sum(values.get(status, (0, 0))[index] for status in ("open", "censored"))
                    for index in (0, 1)
                )
                eligible = (redefault[0] + complete[0], redefault[1] + complete[1])
                total = (eligible[0] + censored[0], eligible[1] + censored[1])
                for name, numerator, denominator, observations in (
                    ("trigger_cohort_count", total[0], None, total[0]),
                    ("trigger_cohort_upb", total[1], None, total[0]),
                    ("redefault_count", redefault[0], eligible[0], eligible[0]),
                    ("redefault_upb", redefault[1], eligible[1], eligible[0]),
                    ("right_censored_count", censored[0], total[0], total[0]),
                    ("right_censored_upb", censored[1], total[1], total[0]),
                ):
                    rows.append(component(
                        "new_delinquency_redefault", name, period, view,
                        "redefault_trigger", trigger, numerator, denominator,
                        observations,
                    ))
    return rows


def build(
    sources: Iterable[Mapping[str, Any]],
    partition_root: Path,
    work_database: Path,
    output: sqlite3.Connection,
    transition_rules: Mapping[str, Any],
) -> dict[str, int]:
    ordered = sorted(sources, key=lambda item: (
        item["report_period"], item["source_family"], item["source_file"]
    ))
    periods = sorted({item["report_period"] for item in ordered})
    by_period = {
        period: [item for item in ordered if item["report_period"] == period]
        for period in periods
    }
    work_database.unlink(missing_ok=True)
    components: dict[tuple[Any, ...], tuple[int, int | None, int]] = {}
    scanned = 0
    try:
        with closing(sqlite3.connect(work_database)) as history:
            history.executescript(HISTORY_SCHEMA)
            history.create_function("month_index", 1, month_index, deterministic=True)
            prior_period: str | None = None
            for period in periods:
                scanned += stage_period(history, by_period[period], partition_root, period)
                for view in VIEWS:
                    key = ("delinquency_roll_cure", "eligible_origin_count", period,
                           view, "loan-cohort", "portfolio", "All")
                    components[key] = (0, None, 0)
                if prior_period is not None:
                    advance_cohorts(
                        history, prior_period, period,
                        transition_rules["delinquency_threshold_days"],
                        transition_rules["redefault_window_months"],
                    )
                    if adjacent_month(prior_period, period):
                        for view in VIEWS:
                            add_interval_components(components, history, period, view)
                        insert_triggers(
                            history, period,
                            transition_rules["delinquency_threshold_days"],
                        )
                history.execute("DELETE FROM prior_history")
                history.execute("INSERT INTO prior_history SELECT * FROM current_history")
                history.commit()
                prior_period = period
            rows = [
                component(
                    key[0], key[1], key[2], key[3], key[5], key[6], *values
                )
                for key, values in components.items()
            ]
            rows.extend(cohort_component_rows(history, periods))
            output.execute("DELETE FROM transition_component")
            output.executemany("INSERT INTO transition_component VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
            output.commit()
            return {
                "history_rows": scanned,
                "history_components": len(rows),
                "history_peak_bytes": work_database.stat().st_size,
            }
    finally:
        work_database.unlink(missing_ok=True)
