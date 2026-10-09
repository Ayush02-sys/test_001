from flask import Blueprint, jsonify, render_template
from ..services.analytics import analytics
from ..utils import require

bp = Blueprint("analytics", __name__)


@bp.route("/analytics")
@require("supervisor")
def page():
    return render_template("analytics.html", d=analytics())


@bp.route("/api/analytics")
@require("supervisor")
def api():
    return jsonify(analytics())
