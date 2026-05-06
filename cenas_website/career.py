# cenas_website/career.py
import os
from flask import Blueprint, render_template, abort

career = Blueprint("career", __name__)

LOCATION_CONFIG = {
    "tomball": {
        "label": "Tomball",
        "formspree": os.environ.get("FORMSPREE_TOMBALL"),
    },
    "copperfield": {
        "label": "Copperfield",
        "formspree": os.environ.get("FORMSPREE_COPPERFIELD"),
    },
}

@career.route("/apply/<slug>", methods=["GET"])
def apply(slug):
    loc = LOCATION_CONFIG.get(slug)
    if not loc:
        abort(404)
    return render_template(
        "apply.html",
        location_slug=slug,
        location_label=loc["label"],
        form_action=loc.get("formspree") or "",
    )

