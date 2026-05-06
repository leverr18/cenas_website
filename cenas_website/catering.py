import os
from flask import Blueprint, render_template, abort, request

catering = Blueprint("catering", __name__)

LOCATION_CONFIG = {
    "tomball": {
        "label": "Tomball",
        "formspree": os.environ.get("FORMSPREE_CATERING_TOMBALL"),
    },
    "copperfield": {
        "label": "Copperfield",
        "formspree": os.environ.get("FORMSPREE_CATERING_COPPERFIELD")
    }
}

@catering.route("/catering/<slug>", methods=["GET"])
def catering_form(slug):
    loc = LOCATION_CONFIG.get(slug)
    if not loc:
        abort(404)

    return render_template(
        "catering_form.html",
        location_slug=slug,
        location_label=loc["label"],
        form_action=loc.get("formspree") or "",
    )