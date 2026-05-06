import os
from flask import Blueprint, render_template, request, url_for, redirect, flash, current_app, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import db
from .models import TrainingVideo
from .forms import TrainingUploadForm, TrainingEditForm, CATEGORY_BY_ROLE

training = Blueprint("training", __name__)

def is_admin():
    return getattr(current_user, "id", None) == 1

# ---------- INDEX ----------
@training.route("/training")
@login_required
def index():
    # role: bartender/server/cashier/host/all
    # cat: a specific subcategory like "coffee"
    role = (request.args.get("role") or "").lower()
    cat = (request.args.get("cat") or "").lower()

    q = TrainingVideo.query

    if cat and cat != "all":
        # Filter by a specific subcategory (we store subcats as lowercase strings)
        q = q.filter(TrainingVideo.category == cat)
    elif role and role != "all":
        # If no specific subcat, but role chosen → show all subcats for that role
        allowed = [val for (val, _label) in CATEGORY_BY_ROLE.get(role, [])]
        if allowed:
            q = q.filter(TrainingVideo.category.in_(allowed))

    videos = q.order_by(TrainingVideo.uploaded_at.desc()).all()

    return render_template(
        "training_index.html",
        videos=videos,
        CATEGORY_BY_ROLE=CATEGORY_BY_ROLE,  # needed for JS
        active_role=role or "all",
        active_cat=cat or "",
    )


# ---------- UPLOAD ----------
@training.route("/training/upload", methods=["GET", "POST"])
@login_required
def upload():
    if not is_admin():
        flash("Access denied.", "error")
        return redirect(url_for("training.index"))

    form = TrainingUploadForm()
    selected_role = form.role.data or next(iter(CATEGORY_BY_ROLE.keys()))
    form.category.choices = CATEGORY_BY_ROLE.get(selected_role, [])

    if form.validate_on_submit():
        file = form.video_file.data
        filename = secure_filename(file.filename)
        training_dir = current_app.config["TRAINING_MEDIA"]
        os.makedirs(training_dir, exist_ok=True)

        # Ensure unique filename
        base, ext = os.path.splitext(filename)
        final = filename
        i = 1
        while os.path.exists(os.path.join(training_dir, final)):
            final = f"{base}_{i}{ext}"
            i += 1

        save_path = os.path.join(training_dir, final)
        file.save(save_path)

        video = TrainingVideo(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            category=form.category.data,
            file_path=final,  # store filename only
            uploaded_by=current_user.id,
        )
        db.session.add(video)
        db.session.commit()
        flash("Video uploaded successfully.", "success")
        return redirect(url_for("training.manage"))

    return render_template("training_upload.html", form=form, CATEGORY_BY_ROLE=CATEGORY_BY_ROLE)

# ---------- STREAM ----------
@training.route("/training/stream/<int:vid>")
@login_required
def stream(vid):
    video = TrainingVideo.query.get_or_404(vid)
    path = os.path.join(current_app.config["TRAINING_MEDIA"], video.file_path)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype=_guess_mime(path))

def _guess_mime(path):
    ext = os.path.splitext(path)[1].lower().strip(".")
    return {
        "mp4": "video/mp4",
        "m4v": "video/mp4",
        "webm": "video/webm",
        "mov": "video/quicktime",
    }.get(ext, "application/octet-stream")

# ---------- MANAGE / EDIT / DELETE ----------
@training.route("/training/manage")
@login_required
def manage():
    if not is_admin():
        flash("Access denied.", "error")
        return redirect(url_for("training.index"))
    videos = TrainingVideo.query.order_by(TrainingVideo.uploaded_at.desc()).all()
    return render_template("training_manage.html", videos=videos)

@training.route("/training/delete/<int:vid>", methods=["POST"])
@login_required
def delete(vid):
    if not is_admin():
        flash("Access denied.", "error")
        return redirect(url_for("training.index"))
    video = TrainingVideo.query.get_or_404(vid)
    file_path = os.path.join(current_app.config["TRAINING_MEDIA"], video.file_path)
    if os.path.isfile(file_path):
        os.remove(file_path)
    db.session.delete(video)
    db.session.commit()
    flash("Video deleted.", "info")
    return redirect(url_for("training.manage"))

# ---------- VIEW ----------
@training.route("/training/view/<int:vid>")
@login_required
def view(vid):
    video = TrainingVideo.query.get_or_404(vid)
    mime=_guess_mime(video.file_path)
    return render_template("training_view.html", video=video)


# ---------- EDIT ----------
@training.route("/training/edit/<int:vid>", methods=["GET", "POST"])
@login_required
def edit(vid):
    if getattr(current_user, "id", None) != 1:
        flash("Access denied.", "error")
        return redirect(url_for("training.index"))

    video = TrainingVideo.query.get_or_404(vid)
    form = TrainingEditForm()

    # Build category choices based on current role selection (default bartender for now)
    selected_role = form.role.data or "bartender"
    form.category.choices = CATEGORY_BY_ROLE.get(selected_role, [])

    if form.validate_on_submit():
        # basic fields
        video.title = form.title.data.strip()
        video.description = (form.description.data or "").strip()
        # store subcategory (lowercase for consistency)
        video.category = (form.category.data or "").lower()

        # optional file replacement
        if form.video_file.data:
            f = form.video_file.data
            fname = secure_filename(f.filename)
            base, ext = os.path.splitext(fname)
            training_dir = current_app.config["TRAINING_MEDIA"]
            os.makedirs(training_dir, exist_ok=True)

            final = fname
            i = 1
            while os.path.exists(os.path.join(training_dir, final)):
                final = f"{base}_{i}{ext}"
                i += 1

            path = os.path.join(training_dir, final)
            f.save(path)
            # store filename only (we prepend TRAINING_MEDIA when streaming)
            video.file_path = final

        db.session.commit()
        flash("Video updated.", "success")
        return redirect(url_for("training.manage"))

    # Prefill form on GET
    if request.method == "GET":
        form.title.data = video.title
        form.description.data = video.description
        # We don’t store role in DB, only the subcategory; default role selector to bartender
        form.role.data = "bartender"
        form.category.choices = CATEGORY_BY_ROLE.get("bartender", [])
        form.category.data = video.category

    return render_template("training_edit.html", form=form, CATEGORY_BY_ROLE=CATEGORY_BY_ROLE)

