#!/usr/bin/env python3
"""案件の集計（ステージ別金額・停滞案件・期限超過・前週差分）をMarkdownで出力する。

会議資料の数値はAgentに計算させず、この処理の出力を使う（AGENTS.md「数値は計算処理で出す」）。
定義は knowledge/playbook/deal-stage-definitions.md に合わせている。

使い方:
  python3 scripts/pipeline_summary.py --as-of 2026-10-01
  python3 scripts/pipeline_summary.py --as-of 2026-09-24 --previous 2026-09-17   # 前週スナップショットがない場合は差分を省略
"""
import argparse
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "data" / "crm" / "snapshots"

# ステージごとの受注確度（deal-stage-definitions.md と同じ値）
PROBABILITY = {"S1": 0.10, "S2": 0.25, "S3": 0.50, "S4": 0.75, "S5": 0.90}
STAGE_ORDER = ["S1 初回接触", "S2 課題確認", "S3 提案", "S4 稟議・条件調整", "S5 契約手続き"]
STALE_NO_ACTIVITY_DAYS = 14   # 最終活動からこの日数以上
STALE_SAME_STAGE_DAYS = 30    # 同じステージにこの日数以上


def load(as_of: str):
    path = SNAPSHOTS / as_of / "deals.csv"
    if not path.exists():
        return None, path
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f)), path


def d(s: str):
    return date.fromisoformat(s) if s else None


def yen(n: float) -> str:
    return f"{n / 1_000_000:,.1f}百万円"


def is_open(deal) -> bool:
    return deal["stage"][:2] in PROBABILITY


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", required=True, help="集計の基準日（スナップショットのフォルダ名 YYYY-MM-DD）")
    ap.add_argument("--previous", help="前週のスナップショット（省略時は基準日の7日前）")
    args = ap.parse_args()

    deals, path = load(args.as_of)
    if deals is None:
        sys.exit(f"スナップショットが見つかりません: {path}")
    today = d(args.as_of)
    prev_key = args.previous or (today - timedelta(days=7)).isoformat()
    prev, prev_path = load(prev_key)

    print(f"# 案件集計（基準日 {args.as_of}）\n")
    print(f"出典: `{path.relative_to(ROOT)}`" + (f"、前週比較: `{prev_path.relative_to(ROOT)}`" if prev else "（前週スナップショットなし）"))
    print()

    # 1. ステージ別
    open_deals = [x for x in deals if is_open(x)]
    print("## ステージ別（進行中の案件）\n")
    print("| ステージ | 件数 | 金額 | 確度 | 加重見込み |")
    print("|---|---:|---:|---:|---:|")
    tot_n = tot_amt = tot_w = 0
    for st in STAGE_ORDER:
        rows = [x for x in open_deals if x["stage"] == st]
        amt = sum(int(x["amount_jpy"]) for x in rows)
        p = PROBABILITY[st[:2]]
        tot_n, tot_amt, tot_w = tot_n + len(rows), tot_amt + amt, tot_w + amt * p
        print(f"| {st} | {len(rows)} | {yen(amt)} | {int(p * 100)}% | {yen(amt * p)} |")
    print(f"| 合計 | {tot_n} | {yen(tot_amt)} | — | {yen(tot_w)} |\n")

    # 2. 受注・失注（今週）
    closed = [x for x in deals if x["stage"] in ("受注", "失注") and d(x["stage_since"]) > today - timedelta(days=7)]
    print("## 今週の受注・失注\n")
    if closed:
        for x in closed:
            note = f"（{x['notes']}）" if x["notes"] else ""
            print(f"* {x['stage']}：{x['company']}（{x['deal_id']}／{x['owner']}）{yen(int(x['amount_jpy']))}{note}")
    else:
        print("* なし")
    print()

    # 3. 今月・来月のクローズ予定
    print("## クローズ予定（進行中の案件）\n")
    for label, (y, m) in (("今月", (today.year, today.month)), ("来月", ((today.year + (today.month == 12)), today.month % 12 + 1))):
        rows = [x for x in open_deals if d(x["expected_close"]).year == y and d(x["expected_close"]).month == m]
        amt = sum(int(x["amount_jpy"]) for x in rows)
        w = sum(int(x["amount_jpy"]) * PROBABILITY[x["stage"][:2]] for x in rows)
        names = "、".join(f"{x['company']}（{x['stage'][:2]}）" for x in rows) or "なし"
        print(f"* {label}（{y}-{m:02d}）：{len(rows)}件／{yen(amt)}（加重 {yen(w)}）— {names}")
    print()

    # 4. 停滞案件
    print(f"## 停滞案件（最終活動から{STALE_NO_ACTIVITY_DAYS}日以上、または同じステージに{STALE_SAME_STAGE_DAYS}日以上）\n")
    print("| 案件 | 担当 | ステージ | 最終活動 | 経過日数 | ステージ滞在 | 理由 |")
    print("|---|---|---|---|---:|---:|---|")
    stale = 0
    for x in open_deals:
        no_act = (today - d(x["last_activity"])).days
        in_stage = (today - d(x["stage_since"])).days
        reasons = []
        if no_act >= STALE_NO_ACTIVITY_DAYS:
            reasons.append("活動なし")
        if in_stage >= STALE_SAME_STAGE_DAYS:
            reasons.append("ステージ滞留")
        if reasons:
            stale += 1
            print(f"| {x['company']}（{x['deal_id']}） | {x['owner']} | {x['stage']} | {x['last_activity']} | {no_act}日 | {in_stage}日 | {'・'.join(reasons)} |")
    if not stale:
        print("| なし | | | | | | |")
    print()

    # 5. 期限超過の次アクション
    print("## 期限を過ぎた次アクション\n")
    over = [x for x in open_deals if x["next_action_due"] and d(x["next_action_due"]) < today]
    for x in over:
        print(f"* {x['company']}（{x['owner']}）：{x['next_action']}（期限 {x['next_action_due']}、{(today - d(x['next_action_due'])).days}日超過）")
    if not over:
        print("* なし")
    print()

    # 6. 前週からの変化
    print("## 前週からの変化\n")
    if not prev:
        print("* 前週スナップショットがないため省略")
        return
    before = {x["deal_id"]: x for x in prev}
    changes = []
    for x in deals:
        b = before.get(x["deal_id"])
        if b is None:
            changes.append(f"* 新規：{x['company']}（{x['stage']}／{yen(int(x['amount_jpy']))}／{x['owner']}）")
        elif b["stage"] != x["stage"]:
            changes.append(f"* ステージ変更：{x['company']} {b['stage']} → {x['stage']}")
        elif b["amount_jpy"] != x["amount_jpy"]:
            changes.append(f"* 金額変更：{x['company']} {yen(int(b['amount_jpy']))} → {yen(int(x['amount_jpy']))}")
    print("\n".join(changes) if changes else "* なし")


if __name__ == "__main__":
    main()
