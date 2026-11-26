import json

from django.db.models import Avg, Count, Sum
from django.db.models.functions import Coalesce, TruncMonth


def build_visitation_analytics(logs_qs):
    """Compute PostgreSQL SQL aggregations and Chart.js series from a VisitationLog queryset."""
    totals = logs_qs.aggregate(
        sum_total=Coalesce(Sum("total_visitors"), 0),
        sum_local=Coalesce(Sum("local_visitors"), 0),
        sum_dom=Coalesce(Sum("domestic_visitors"), 0),
        sum_for=Coalesce(Sum("foreign_visitors"), 0),
        avg_daily=Avg("total_visitors"),
        log_count=Count("id"),
    )

    monthly_rows = list(
        logs_qs.annotate(month=TruncMonth("visit_date"))
        .values("month")
        .annotate(visitors=Sum("total_visitors"))
        .order_by("month")
    )

    if len(monthly_rows) >= 2:
        trend_labels = [row["month"].strftime("%b %Y") for row in monthly_rows[-8:]]
        trend_values = [int(row["visitors"] or 0) for row in monthly_rows[-8:]]
    else:
        recent_rows = list(logs_qs.order_by("visit_date")[:10])
        trend_labels = [r.visit_date.strftime("%b %d") for r in recent_rows]
        trend_values = [int(r.total_visitors) for r in recent_rows]

    total = int(totals["sum_total"] or 0)
    local_v = int(totals["sum_local"] or 0)
    dom_v = int(totals["sum_dom"] or 0)
    for_v = int(totals["sum_for"] or 0)

    if total > 0:
        local_pct = round((local_v / total) * 100, 1)
        dom_pct = round((dom_v / total) * 100, 1)
        for_pct = round((for_v / total) * 100, 1)
    else:
        local_pct = dom_pct = for_pct = 0.0

    return {
        "total_visitors": total,
        "local_visitors": local_v,
        "domestic_visitors": dom_v,
        "foreign_visitors": for_v,
        "local_pct": local_pct,
        "domestic_pct": dom_pct,
        "foreign_pct": for_pct,
        "avg_daily": round(float(totals["avg_daily"] or 0), 1) if totals["log_count"] else 0,
        "log_count": int(totals["log_count"] or 0),
        "has_chart_data": bool(trend_labels),
        "trend_labels_json": json.dumps(trend_labels),
        "trend_values_json": json.dumps(trend_values),
        "origin_values_json": json.dumps([local_v, dom_v, for_v]),
    }
