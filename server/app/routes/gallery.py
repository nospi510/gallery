from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_login import login_required, current_user
from ..models.models import Photo, User
from ..forms.forms import AddPhotoForm, EditProfileForm
from ..extensions import db
from PIL import Image
import os
import pyheif
import secrets
from sqlalchemy import func

gallery_bp = Blueprint('gallery', __name__)

# Route pour voir une photo spécifique par ID
@gallery_bp.route('/view_photo/<int:photo_id>')
def view_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    return send_from_directory('static/images', photo.image)

# Route pour charger plus de photos via AJAX
@gallery_bp.route('/load_more_photos/<int:user_id>', methods=['GET'])
@login_required
def load_more_photos(user_id):
    offset = int(request.args.get('offset', 0))
    limit = 4  # Charger 4 photos à la fois
    photos = Photo.query.filter_by(user_id=user_id).order_by(Photo.date_posted.desc()).offset(offset).limit(limit).all()
    has_more = Photo.query.filter_by(user_id=user_id).count() > offset + len(photos)
    
    return jsonify({
        'status': 'success',
        'photos': [{'image': photo.image} for photo in photos],
        'has_more': has_more
    })

# Route pour le tableau de bord de l'utilisateur
@gallery_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    sort_order = request.args.get('sort_order', 'recent')
    if sort_order == 'recent':
        user_photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.date_posted.desc()).all()
    elif sort_order == 'old':
        user_photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.date_posted.asc()).all()
    else:
        user_photos = Photo.query.filter_by(user_id=current_user.id).all()

    if request.is_json:
        return jsonify({
            "status": "success",
            "photos": [photo.to_dict() for photo in user_photos]
        }), 200

    return render_template('dashboard.html', user_photos=user_photos, sort_order=sort_order)

# Route pour modifier le profil de l'utilisateur
@gallery_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        current_user.username = form.username.data

        if form.password.data:
            current_user.set_password(form.password.data)

        db.session.commit()
        flash('Profil mis à jour avec succès!', 'success')

        if request.is_json:
            return jsonify({"status": "success", "message": "Profil mis à jour avec succès!"}), 200

        return redirect(url_for('gallery.dashboard'))

    if request.method == 'GET' and request.is_json:
        return jsonify({
            "status": "success",
            "username": current_user.username,
        }), 200

    form.username.data = current_user.username
    return render_template('edit_profile.html', form=form)

# Fonction pour convertir les fichiers HEIC en JPEG
def convert_heic_to_jpeg(heic_file):
    heif_file = pyheif.read(heic_file)
    image = Image.frombytes(
        heif_file.mode, 
        heif_file.size, 
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    return image

# Fonction pour sauvegarder une photo
def save_photo(photo):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(photo.filename)
    f_ext = f_ext.lower()
    photo_fn = random_hex + ('.jpg' if f_ext == '.heic' else f_ext)
    photo_path = os.path.join(os.path.dirname(__file__), '../static/images', photo_fn)

    if f_ext == '.heic':
        image = convert_heic_to_jpeg(photo)
        image.save(photo_path, 'JPEG')
    else:
        photo.save(photo_path)

    return photo_fn

# Route pour ajouter une photo
@gallery_bp.route('/add_photo', methods=['GET', 'POST'])
@login_required
def add_photo():
    form = AddPhotoForm()
    if form.validate_on_submit():
        for uploaded_file in request.files.getlist('image'):
            if uploaded_file.filename != '':
                filename = save_photo(uploaded_file)
                new_photo = Photo(image=filename, user_id=current_user.id)
                db.session.add(new_photo)
                db.session.commit()

        flash('Photos ajoutées avec succès!', 'success')

        if request.is_json:
            return jsonify({"status": "success", "message": "Photos ajoutées avec succès!"}), 200

        return redirect(url_for('gallery.gallery'))

    if request.method == 'GET' and request.is_json:
        return jsonify({
            "status": "success",
            "message": "Ajoutez une nouvelle photo.",
        }), 200

    return render_template('add_photo.html', form=form)

# Route principale de la galerie
@gallery_bp.route('/', methods=['GET'])
@login_required
def gallery():
    sort_option = request.args.get('sort', 'none')
    search_query = request.args.get('search', '')

    if search_query:
        users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
    else:
        if sort_option == 'az':
            users = User.query.order_by(User.username.asc()).all()
        elif sort_option == 'za':
            users = User.query.order_by(User.username.desc()).all()
        elif sort_option == 'recent':
            users = User.query.join(Photo).group_by(User.id).order_by(func.max(Photo.date_posted).desc()).all()
        elif sort_option == 'old':
            users = User.query.join(Photo).group_by(User.id).order_by(func.max(Photo.date_posted).asc()).all()
        else:
            users = User.query.all()

    if request.is_json:
        return jsonify({
            "status": "success",
            "users": [user.to_dict() for user in users],
            "sort_option": sort_option,
            "search_query": search_query
        }), 200

    return render_template('gallery.html', users=users, sort_option=sort_option, search_query=search_query)