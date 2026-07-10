"""Deterministic vendor scoring. No LLM anywhere in this file.

Four dimensions (0-100 each), weighted into an overall score:
  price 35% · delivery confidence 25% · documentation 15% · reliability 25%
"""
from datetime import date, timedelta

WEIGHTS = {"price": 0.35, "delivery": 0.25, "docs": 0.15, "reliability": 0.25}


def price_score(normalized: float | None, best: float, budget: float | None) -> tuple[float, str]:
    if normalized is None:
        return 0.0, "no usable price"
    # 100 for the cheapest, minus 4 points per % above the cheapest
    pct_over_best = (normalized - best) / best * 100 if best else 0
    score = max(0.0, 100 - pct_over_best * 4)
    evidence = f"₹{normalized:g} vs best ₹{best:g} ({pct_over_best:+.1f}%)"
    if budget:
        evidence += f"; budget ₹{budget:g} — {'within' if normalized <= budget else 'OVER'} budget"
        if normalized > budget:
            score = max(0.0, score - 15)
    return round(score, 1), evidence


def delivery_score(fields: dict, deadline: date | None) -> tuple[float, str]:
    days = fields.get("delivery_days")
    promised: date | None = fields.get("delivery_date")
    vague = fields.get("delivery_vague", False)

    if promised is None and days is not None:
        promised = date.today() + timedelta(days=int(days))

    if promised is None:
        if vague:
            return 15.0, "evasive answer, no committed timeline"
        return 30.0, "no delivery timeline given"

    score, evidence = 85.0, f"promised {promised.isoformat()}"
    if deadline:
        buffer_days = (deadline - promised).days
        if buffer_days >= 5:
            score, evidence = 95.0, f"{evidence} — {buffer_days} days before deadline"
        elif buffer_days >= 0:
            score, evidence = 75.0, f"{evidence} — only {buffer_days} days of buffer"
        else:
            score, evidence = 20.0, f"{evidence} — MISSES deadline by {-buffer_days} days"
    if vague:
        score = max(10.0, score - 30)
        evidence += "; hedged with vague language"
    return round(score, 1), evidence


def doc_score(cert_attached: bool, cert_statuses: list[str], certs_required: bool) -> tuple[float, str]:
    score, parts = 50.0, []
    if cert_attached:
        score += 25
        parts.append("certificate attached with quote")
    valid = [s for s in cert_statuses if s == "valid"]
    problems = [s for s in cert_statuses if s in ("expired", "invalid_format", "missing_number")]
    if valid:
        score += 25
        parts.append(f"{len(valid)} valid certificate(s) on file")
    if problems:
        score -= 25 * len(problems)
        parts.append(f"certificate issues: {', '.join(problems)}")
    if certs_required and not (cert_attached or valid):
        score -= 30
        parts.append("certificate mandatory but none verified")
    return round(min(100.0, max(0.0, score)), 1), "; ".join(parts) or "no documentation signals"


def reliability_from_memory(memory) -> tuple[float, str]:
    if memory is None or memory.rfq_count == 0:
        return 50.0, "no history — neutral score"
    parts = [f"{memory.rfq_count} past RFQ(s)"]
    if memory.avg_response_hours is not None:
        parts.append(f"avg response {memory.avg_response_hours:g}h")
    parts.append(f"on-time rate {memory.on_time_rate:.0%}")
    if memory.ghost_count:
        parts.append(f"ghosted {memory.ghost_count}x")
    return round(memory.reliability_score, 1), "; ".join(parts)


def overall(p: float, d: float, doc: float, r: float) -> float:
    return round(
        p * WEIGHTS["price"] + d * WEIGHTS["delivery"] + doc * WEIGHTS["docs"] + r * WEIGHTS["reliability"], 1
    )