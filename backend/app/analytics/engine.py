"""
Phase 16 - Analytics & Trend Engine.
Computes real database-backed KPIs, label distribution breakdowns,
and robust period-over-period trend calculations with zero-division safety.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.ticket import Ticket


def calculate_percentage_change(current: int, previous: int) -> Tuple[float, str]:
    """
    Computes percentage change: (current - previous) / previous * 100
    Handles zero-denominator cases cleanly.
    Returns: (percentage_change, direction: "UP" | "DOWN" | "FLAT")
    """
    if previous == 0:
        if current == 0:
            return 0.0, "FLAT"
        return 100.0, "UP"

    pct = round(((current - previous) / previous) * 100.0, 1)
    if pct > 0:
        direction = "UP"
    elif pct < 0:
        direction = "DOWN"
    else:
        direction = "FLAT"

    return pct, direction


def get_analytics_summary(db: Session) -> Dict:
    """Computes real-time executive dashboard KPIs from the database."""
    total_tickets = db.query(Ticket).count()

    if total_tickets == 0:
        return {
            "total_tickets": 0,
            "auto_routed_count": 0,
            "human_review_count": 0,
            "auto_routing_rate": 0.0,
            "avg_confidence": 0.0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "categories": {"Billing": 0, "Technical": 0, "Account": 0, "Refund": 0, "General": 0},
            "priorities": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            "departments": {"Finance": 0, "Technical": 0, "Account": 0, "Refunds": 0, "General Support": 0},
        }

    auto_routed = db.query(Ticket).filter(Ticket.routing_status == "AUTO_ROUTED").count()
    human_review = db.query(Ticket).filter(Ticket.routing_status == "HUMAN_REVIEW").count()
    auto_routing_rate = round((auto_routed / total_tickets) * 100, 1)

    avg_conf = db.query(func.avg(Ticket.confidence)).scalar() or 0.0

    # Category breakdown
    cat_counts = dict(
        db.query(Ticket.final_category, func.count(Ticket.id)).group_by(Ticket.final_category).all()
    )
    categories = {
        "Billing": cat_counts.get("Billing", 0),
        "Technical": cat_counts.get("Technical", 0),
        "Account": cat_counts.get("Account", 0),
        "Refund": cat_counts.get("Refund", 0),
        "General": cat_counts.get("General", 0),
    }

    # Priority breakdown
    pri_counts = dict(
        db.query(Ticket.final_priority, func.count(Ticket.id)).group_by(Ticket.final_priority).all()
    )
    priorities = {
        "Critical": pri_counts.get("Critical", 0),
        "High": pri_counts.get("High", 0),
        "Medium": pri_counts.get("Medium", 0),
        "Low": pri_counts.get("Low", 0),
    }

    # Department breakdown
    dept_counts = dict(
        db.query(Ticket.final_department, func.count(Ticket.id)).group_by(Ticket.final_department).all()
    )
    departments = {
        "Finance": dept_counts.get("Finance", 0),
        "Technical": dept_counts.get("Technical", 0),
        "Account": dept_counts.get("Account", 0),
        "Refunds": dept_counts.get("Refunds", 0),
        "General Support": dept_counts.get("General Support", 0),
    }

    return {
        "total_tickets": total_tickets,
        "auto_routed_count": auto_routed,
        "human_review_count": human_review,
        "auto_routing_rate": auto_routing_rate,
        "avg_confidence": round(float(avg_conf), 3),
        "critical_count": priorities["Critical"],
        "high_count": priorities["High"],
        "medium_count": priorities["Medium"],
        "low_count": priorities["Low"],
        "categories": categories,
        "priorities": priorities,
        "departments": departments,
    }


def get_analytics_trends(db: Session, days_window: int = 7) -> Dict:
    """
    Computes period-over-period trend deltas comparing current N days vs preceding N days.
    """
    now = datetime.utcnow()
    current_start = now - timedelta(days=days_window)
    previous_start = current_start - timedelta(days=days_window)

    def count_period(filter_expr):
        curr = (
            db.query(Ticket)
            .filter(Ticket.created_at >= current_start, Ticket.created_at <= now)
            .filter(filter_expr)
            .count()
        )
        prev = (
            db.query(Ticket)
            .filter(Ticket.created_at >= previous_start, Ticket.created_at < current_start)
            .filter(filter_expr)
            .count()
        )
        return curr, prev

    # Summary metric trends
    curr_total, prev_total = count_period(True)
    curr_auto, prev_auto = count_period(Ticket.routing_status == "AUTO_ROUTED")
    curr_rev, prev_rev = count_period(Ticket.routing_status == "HUMAN_REVIEW")

    def make_trend_item(name, curr, prev):
        pct, direction = calculate_percentage_change(curr, prev)
        return {
            "name": name,
            "current": curr,
            "previous": prev,
            "percentage_change": pct,
            "direction": direction,
        }

    summary_trends = [
        make_trend_item("Total Volume", curr_total, prev_total),
        make_trend_item("Auto-Routed", curr_auto, prev_auto),
        make_trend_item("Review Queue", curr_rev, prev_rev),
    ]

    # Category trends
    category_trends = []
    for cat in ["Billing", "Technical", "Account", "Refund", "General"]:
        curr_c, prev_c = count_period(Ticket.final_category == cat)
        category_trends.append(make_trend_item(cat, curr_c, prev_c))

    # Priority trends
    priority_trends = []
    for pri in ["Critical", "High", "Medium", "Low"]:
        curr_p, prev_p = count_period(Ticket.final_priority == pri)
        priority_trends.append(make_trend_item(pri, curr_p, prev_p))

    # Department trends
    department_trends = []
    for dept in ["Finance", "Technical", "Account", "Refunds", "General Support"]:
        curr_d, prev_d = count_period(Ticket.final_department == dept)
        department_trends.append(make_trend_item(dept, curr_d, prev_d))

    return {
        "summary_trends": summary_trends,
        "category_trends": category_trends,
        "priority_trends": priority_trends,
        "department_trends": department_trends,
    }
