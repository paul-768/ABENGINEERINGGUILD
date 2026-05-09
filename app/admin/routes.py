# app/admin/routes.py - COMPLETE FIXED VERSION (NO DUPLICATES)
from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Topic, Question, QuizResult, Post, Notification, Announcement, MaterialLink, ABELELink
from app.admin.forms import QuestionForm, TopicForm, AnnouncementForm
from app.admin import admin_bp
from datetime import datetime, timedelta
import os
import json

# Allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_multiple_images(files, subfolder='announcements'):
    """Save multiple images and return list of paths"""
    if not files:
        return []
    
    saved_images = []
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_folder, exist_ok=True)
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                saved_images.append(f"uploads/{subfolder}/{unique_filename}")
    
    return saved_images

def save_file(file, subfolder='announcements'):
    """Save uploaded file and return file info"""
    if not file or file.filename == '':
        return None, None, None, None
    
    if not allowed_file(file.filename):
        return None, None, None, None
    
    filename = secure_filename(file.filename)
    name_parts = filename.rsplit('.', 1)
    unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{name_parts[0]}.{name_parts[1]}"
    
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        file_type = 'image'
    elif ext == 'pdf':
        file_type = 'pdf'
    elif ext in ['doc', 'docx']:
        file_type = 'document'
    elif ext in ['xls', 'xlsx']:
        file_type = 'spreadsheet'
    else:
        file_type = 'other'
    
    file_size = os.path.getsize(file_path)
    relative_path = f"uploads/{subfolder}/{unique_filename}"
    
    return relative_path, filename, file_size, file_type

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    total_users = User.query.count()
    total_topics = Topic.query.count()
    total_questions = Question.query.count()
    total_quizzes = QuizResult.query.count()
    total_posts = Post.query.count()
    total_announcements = Announcement.query.count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_quizzes = QuizResult.query.options(
        db.joinedload(QuizResult.user),
        db.joinedload(QuizResult.topic)
    ).order_by(QuizResult.completed_at.desc()).limit(10).all()
    
    today = datetime.utcnow().date()
    quizzes_today = QuizResult.query.filter(
        db.func.date(QuizResult.completed_at) == today
    ).count()
    
    new_users_today = User.query.filter(
        db.func.date(User.created_at) == today
    ).count()
    
    recent_announcements = Announcement.query.order_by(
        Announcement.created_at.desc()
    ).limit(5).all()
    
    from datetime import datetime as dt
    now = dt.now()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_topics=total_topics,
                         total_questions=total_questions,
                         total_quizzes=total_quizzes,
                         total_posts=total_posts,
                         total_announcements=total_announcements,
                         recent_users=recent_users,
                         recent_quizzes=recent_quizzes,
                         recent_announcements=recent_announcements,
                         quizzes_today=quizzes_today,
                         new_users_today=new_users_today,
                         now=now,
                         title='Admin Dashboard')


@admin_bp.route('/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/manage_users.html',
                         users=users,
                         title='Manage Users')


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        secret_key = data.get('secret_key', '')
        make_admin = data.get('make_admin', True)
        
        SECRET_KEY = "Luffy will be the King of the Pirates!"
        
        if secret_key != SECRET_KEY:
            return jsonify({'success': False, 'message': 'Invalid authorization key! Access denied.'}), 403
        
        user = User.query.get_or_404(user_id)
        
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot modify your own admin status'}), 400
        
        user.is_admin = make_admin
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Admin status updated for {user.name}'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== TOPIC ROUTES ====================

@admin_bp.route('/topics')
@login_required
def manage_topics():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    topics = Topic.query.order_by(Topic.id.asc()).all()
    return render_template('admin/manage_topics.html',
                         topics=topics,
                         title='Manage Topics')


@admin_bp.route('/api/topic/<int:topic_id>')
@login_required
def get_topic_api(topic_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        topic = Topic.query.get_or_404(topic_id)
        return jsonify({
            'success': True,
            'topic': {
                'id': topic.id,
                'name': topic.name,
                'description': topic.description or '',
                'icon': topic.icon,
                'color': topic.color
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/topics/create', methods=['POST'])
@login_required
def create_topic():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', 'fas fa-folder')
    color = request.form.get('color', '#4CAF50')
    
    if not name:
        flash('Topic name is required', 'danger')
        return redirect(url_for('admin.manage_topics'))
    
    topic = Topic(name=name, description=description, icon=icon, color=color)
    db.session.add(topic)
    db.session.commit()
    
    flash(f'Topic "{name}" created successfully!', 'success')
    return redirect(url_for('admin.manage_topics'))


@admin_bp.route('/topics/<int:topic_id>/edit', methods=['POST'])
@login_required
def edit_topic(topic_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    topic = Topic.query.get_or_404(topic_id)
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', topic.icon)
    color = request.form.get('color', topic.color)
    
    if not name:
        flash('Topic name is required', 'danger')
        return redirect(url_for('admin.manage_topics'))
    
    topic.name = name
    topic.description = description
    topic.icon = icon
    topic.color = color
    
    db.session.commit()
    
    flash(f'Topic "{name}" updated successfully!', 'success')
    return redirect(url_for('admin.manage_topics'))


@admin_bp.route('/topics/<int:topic_id>/delete', methods=['POST'])
@login_required
def delete_topic(topic_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        topic = Topic.query.get_or_404(topic_id)
        
        if topic.questions.count() > 0:
            return jsonify({'success': False, 'message': 'Cannot delete topic with existing questions.'}), 400
        
        name = topic.name
        db.session.delete(topic)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Topic "{name}" deleted!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== QUESTIONS ROUTES ====================

@admin_bp.route('/questions')
@login_required
def manage_questions():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    topics = Topic.query.order_by(Topic.id.asc()).all()
    total_questions = Question.query.count()
    form = QuestionForm()
    form.topic_id.choices = [(t.id, t.name) for t in topics]
    
    return render_template('admin/manage_questions.html',
                         form=form,
                         topics=topics,
                         total_questions=total_questions,
                         title='Manage Questions')


@admin_bp.route('/api/topic/<int:topic_id>/questions')
@login_required
def get_topic_questions_api(topic_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        topic = Topic.query.get_or_404(topic_id)
        questions = []
        for q in topic.questions:
            questions.append({
                'id': q.id,
                'topic_id': q.topic_id,
                'question_text': q.question_text,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation or ''
            })
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/question/<int:question_id>')
@login_required
def get_question_api(question_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        question = Question.query.get_or_404(question_id)
        return jsonify({
            'success': True,
            'question': {
                'id': question.id,
                'topic_id': question.topic_id,
                'question_text': question.question_text,
                'option_a': question.option_a,
                'option_b': question.option_b,
                'option_c': question.option_c,
                'option_d': question.option_d,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation or ''
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/questions/search')
@login_required
def search_questions_api():
    """Search questions across all topics (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    search_term = request.args.get('q', '').strip().lower()
    
    if not search_term:
        return jsonify({'success': True, 'questions': []})
    
    # Search in questions
    questions = Question.query.filter(
        (Question.question_text.ilike(f'%{search_term}%')) |
        (Question.option_a.ilike(f'%{search_term}%')) |
        (Question.option_b.ilike(f'%{search_term}%')) |
        (Question.option_c.ilike(f'%{search_term}%')) |
        (Question.option_d.ilike(f'%{search_term}%')) |
        (Question.explanation.ilike(f'%{search_term}%'))
    ).all()
    
    result = []
    for q in questions:
        result.append({
            'id': q.id,
            'topic_id': q.topic_id,
            'topic_name': q.topic.name if q.topic else 'Unknown',
            'question_text': q.question_text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'correct_answer': q.correct_answer,
            'explanation': q.explanation or ''
        })
    
    return jsonify({'success': True, 'questions': result})


@admin_bp.route('/questions/create', methods=['POST'])
@login_required
def create_question():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        topic_id = request.form.get('topic_id')
        question_text = request.form.get('question_text', '').strip()
        option_a = request.form.get('option_a', '').strip()
        option_b = request.form.get('option_b', '').strip()
        option_c = request.form.get('option_c', '').strip()
        option_d = request.form.get('option_d', '').strip()
        correct_answer = request.form.get('correct_answer', '').upper()
        explanation = request.form.get('explanation', '').strip()
        
        question = Question(
            topic_id=int(topic_id),
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            explanation=explanation
        )
        
        db.session.add(question)
        db.session.commit()
        flash('Question created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_questions'))


@admin_bp.route('/questions/<int:question_id>/edit', methods=['POST'])
@login_required
def edit_question(question_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        question = Question.query.get_or_404(question_id)
        
        question.topic_id = int(request.form.get('topic_id'))
        question.question_text = request.form.get('question_text', '').strip()
        question.option_a = request.form.get('option_a', '').strip()
        question.option_b = request.form.get('option_b', '').strip()
        question.option_c = request.form.get('option_c', '').strip()
        question.option_d = request.form.get('option_d', '').strip()
        question.correct_answer = request.form.get('correct_answer', '').upper()
        question.explanation = request.form.get('explanation', '').strip()
        
        db.session.commit()
        flash('Question updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_questions'))


@admin_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        question = Question.query.get_or_404(question_id)
        db.session.delete(question)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Question deleted!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== ANNOUNCEMENTS ROUTES ====================

@admin_bp.route('/announcements')
@login_required
def manage_announcements():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    form = AnnouncementForm()
    
    return render_template('admin/announcements.html',
                         announcements=announcements,
                         form=form,
                         title='Manage Announcements')


# ==================== MATERIAL LINKS ROUTES ====================

@admin_bp.route('/manage-material-links')
@login_required
def manage_material_links():
    """Manage study material external links (Admin only)"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    topics = ['AREA I', 'AREA II', 'AREA III', 'Engineering Mathematics', 'PAES Standards']
    
    topic_materials = {
        'AREA I': [
            {'id': 1, 'title': '1. Agricultural and Biosystems Power Engineering'},
            {'id': 2, 'title': '2. Agricultural and Biosystems Mechanization Planning, Operation, Maintenance, Management and Manufacturing'},
            {'id': 3, 'title': '3. Agricultural and Biosystems Machinery Specifications, Testing and Evaluation'},
            {'id': 4, 'title': '4. Agricultural and Biosystems Automation, Instrumentation and Control System'},
            {'id': 5, 'title': '5. Project Management, Feasibility Study Preparation/Evaluation, Agricultural and Biosystems Research, Development and Extension'},
            {'id': 6, 'title': '6. Laws, Professional Standards and Ethics'}
        ],
        'AREA II': [
            {'id': 7, 'title': '1. Hydrology'},
            {'id': 8, 'title': '2. Irrigation and Drainage Engineering'},
            {'id': 9, 'title': '3. Soil and Water Resources Engineering'},
            {'id': 10, 'title': '4. Aquaculture Engineering'},
            {'id': 11, 'title': '5. Fundamentals of Agricultural, Fishery, Ecological and Environmental Sciences'},
            {'id': 12, 'title': '6. Mathematics and Basic Engineering'}
        ],
        'AREA III': [
            {'id': 13, 'title': '1. Agricultural Buildings and Structures'},
            {'id': 14, 'title': '2. Farm Electrification'},
            {'id': 15, 'title': '3. Environment Engineering'},
            {'id': 16, 'title': '4. Agricultural and Bioprocess Engineering'},
            {'id': 17, 'title': '5. Food Engineering'}
        ],
        'Engineering Mathematics': [
            {'id': 18, 'title': '1. Mathematics in the Modern World'},
            {'id': 19, 'title': '2. College Algebra'},
            {'id': 20, 'title': '3. Plane and Solid Geometry'},
            {'id': 21, 'title': '4. Trigonometry'},
            {'id': 22, 'title': '5. Analytic Geometry'},
            {'id': 23, 'title': '6. Differential Calculus'},
            {'id': 24, 'title': '7. Integral Calculus'},
            {'id': 25, 'title': '8. Differential Equations'},
            {'id': 26, 'title': '9. Engineering Data Analysis (Probability and Statistics)'},
            {'id': 27, 'title': '10. Advanced Engineering Mathematics'},
            {'id': 28, 'title': '11. Numerical Methods'},
            {'id': 29, 'title': '12. Engineering Economics'},
            {'id': 30, 'title': '13. Fluid Mechanics Mathematics'},
            {'id': 31, 'title': '14. Hydraulics and Hydrology Mathematics'},
            {'id': 32, 'title': '15. Thermodynamics and Heat Transfer Mathematics'},
            {'id': 33, 'title': '16. Engineering Mechanics Mathematics'},
            {'id': 34, 'title': '17. Soil and Water Engineering Mathematics'},
            {'id': 35, 'title': '18. Design Project / Thesis Mathematics'}
        ],
        'PAES Standards': [
            {'id': 36, 'title': 'AMTEC: OFFICIAL WEBSITE'},
            {'id': 37, 'title': 'Agricultural Structures'},
            {'id': 38, 'title': 'Engineering Materials'},
            {'id': 39, 'title': 'Irrigation Structures'},
            {'id': 40, 'title': 'Production Machinery'},
            {'id': 41, 'title': 'Post-Harvest Machinery'}
        ]
    }
    
    # Fetch existing links from database
    all_links = MaterialLink.query.all()
    
    # Create a lookup dictionary for quick access
    link_lookup = {}
    for link in all_links:
        key = f"{link.material_title}_{link.link_name}"
        link_lookup[key] = link
    
    # Attach links to materials
    for topic_name, materials in topic_materials.items():
        for material in materials:
            material_title = material['title']
            material['review_link'] = link_lookup.get(f"{material_title}_Review Materials")
            material['video_link'] = link_lookup.get(f"{material_title}_AB Engineering Guild Videos")
    
    return render_template('admin/manage_material_links.html',
                         topics=topics,
                         topic_materials=topic_materials,
                         title='Manage Material Links')

@admin_bp.route('/api/material/<int:material_id>/link')
@login_required
def get_material_link_api(material_id):
    """Get material link data for editing (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        link_type = request.args.get('type', 'review')
        link_name = 'Review Materials' if link_type == 'review' else 'AB Engineering Guild Videos'
        
        # Get material title from the ID mapping
        material_titles = {
            1: '1. Agricultural and Biosystems Power Engineering',
            2: '2. Agricultural and Biosystems Mechanization Planning, Operation, Maintenance, Management and Manufacturing',
            3: '3. Agricultural and Biosystems Machinery Specifications, Testing and Evaluation',
            4: '4. Agricultural and Biosystems Automation, Instrumentation and Control System',
            5: '5. Project Management, Feasibility Study Preparation/Evaluation, Agricultural and Biosystems Research, Development and Extension',
            6: '6. Laws, Professional Standards and Ethics',
            7: '1. Hydrology',
            8: '2. Irrigation and Drainage Engineering',
            9: '3. Soil and Water Resources Engineering',
            10: '4. Aquaculture Engineering',
            11: '5. Fundamentals of Agricultural, Fishery, Ecological and Environmental Sciences',
            12: '6. Mathematics and Basic Engineering',
            13: '1. Agricultural Buildings and Structures',
            14: '2. Farm Electrification',
            15: '3. Environment Engineering',
            16: '4. Agricultural and Bioprocess Engineering',
            17: '5. Food Engineering',
            18: '1. Mathematics in the Modern World',
            19: '2. College Algebra',
            20: '3. Plane and Solid Geometry',
            21: '4. Trigonometry',
            22: '5. Analytic Geometry',
            23: '6. Differential Calculus',
            24: '7. Integral Calculus',
            25: '8. Differential Equations',
            26: '9. Engineering Data Analysis (Probability and Statistics)',
            27: '10. Advanced Engineering Mathematics',
            28: '11. Numerical Methods',
            29: '12. Engineering Economics',
            30: '13. Fluid Mechanics Mathematics',
            31: '14. Hydraulics and Hydrology Mathematics',
            32: '15. Thermodynamics and Heat Transfer Mathematics',
            33: '16. Engineering Mechanics Mathematics',
            34: '17. Soil and Water Engineering Mathematics',
            35: '18. Design Project / Thesis Mathematics',
            36: 'AMTEC: OFFICIAL WEBSITE',
            37: 'Agricultural Structures',
            38: 'Engineering Materials',
            39: 'Irrigation Structures',
            40: 'Production Machinery',
            41: 'Post-Harvest Machinery'
        }
        
        material_title = material_titles.get(material_id, '')
        
        if not material_title:
            return jsonify({'success': False, 'message': 'Material not found'}), 404
        
        link = MaterialLink.query.filter_by(
            material_title=material_title,
            link_name=link_name
        ).first()
        
        return jsonify({
            'success': True,
            'material_id': material_id,
            'material_title': material_title,
            'link_url': link.link_url if link else '#',
            'link_name': link_name
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/material/<int:material_id>/link/edit', methods=['POST'])
@login_required
def edit_material_link(material_id):
    """Edit a material link (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        link_type = request.form.get('link_type', 'review')
        link_name = 'Review Materials' if link_type == 'review' else 'AB Engineering Guild Videos'
        link_url = request.form.get('link_url', '').strip()
        
        # Material titles mapping (same as above)
        material_titles = {
            1: '1. Agricultural and Biosystems Power Engineering',
            2: '2. Agricultural and Biosystems Mechanization Planning, Operation, Maintenance, Management and Manufacturing',
            3: '3. Agricultural and Biosystems Machinery Specifications, Testing and Evaluation',
            4: '4. Agricultural and Biosystems Automation, Instrumentation and Control System',
            5: '5. Project Management, Feasibility Study Preparation/Evaluation, Agricultural and Biosystems Research, Development and Extension',
            6: '6. Laws, Professional Standards and Ethics',
            7: '1. Hydrology',
            8: '2. Irrigation and Drainage Engineering',
            9: '3. Soil and Water Resources Engineering',
            10: '4. Aquaculture Engineering',
            11: '5. Fundamentals of Agricultural, Fishery, Ecological and Environmental Sciences',
            12: '6. Mathematics and Basic Engineering',
            13: '1. Agricultural Buildings and Structures',
            14: '2. Farm Electrification',
            15: '3. Environment Engineering',
            16: '4. Agricultural and Bioprocess Engineering',
            17: '5. Food Engineering',
            18: '1. Mathematics in the Modern World',
            19: '2. College Algebra',
            20: '3. Plane and Solid Geometry',
            21: '4. Trigonometry',
            22: '5. Analytic Geometry',
            23: '6. Differential Calculus',
            24: '7. Integral Calculus',
            25: '8. Differential Equations',
            26: '9. Engineering Data Analysis (Probability and Statistics)',
            27: '10. Advanced Engineering Mathematics',
            28: '11. Numerical Methods',
            29: '12. Engineering Economics',
            30: '13. Fluid Mechanics Mathematics',
            31: '14. Hydraulics and Hydrology Mathematics',
            32: '15. Thermodynamics and Heat Transfer Mathematics',
            33: '16. Engineering Mechanics Mathematics',
            34: '17. Soil and Water Engineering Mathematics',
            35: '18. Design Project / Thesis Mathematics',
            36: 'AMTEC: OFFICIAL WEBSITE',
            37: 'Agricultural Structures',
            38: 'Engineering Materials',
            39: 'Irrigation Structures',
            40: 'Production Machinery',
            41: 'Post-Harvest Machinery'
        }
        
        material_title = material_titles.get(material_id, '')
        
        if not material_title:
            flash('Material not found', 'danger')
            return redirect(url_for('admin.manage_material_links'))
        
        if not link_url or link_url == '#':
            flash('Please enter a valid URL', 'danger')
            return redirect(url_for('admin.manage_material_links'))
        
        # Find existing link or create new
        link = MaterialLink.query.filter_by(
            material_title=material_title,
            link_name=link_name
        ).first()
        
        # Determine topic_name from material_id
        if material_id <= 6:
            topic_name = 'AREA I'
        elif material_id <= 12:
            topic_name = 'AREA II'
        elif material_id <= 17:
            topic_name = 'AREA III'
        elif material_id <= 35:
            topic_name = 'Engineering Mathematics'
        else:
            topic_name = 'PAES Standards'
        
        if link:
            link.link_url = link_url
            link.updated_at = datetime.utcnow()
        else:
            link = MaterialLink(
                material_id=material_id,
                topic_name=topic_name,
                material_title=material_title,
                link_name=link_name,
                link_url=link_url,
                link_type='google_drive' if 'drive' in link_url else 'youtube',
                display_order=0
            )
            db.session.add(link)
        
        db.session.commit()
        flash('Link updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating link: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_material_links'))


@admin_bp.route('/manage-links')
@login_required
def manage_links():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    material_links = MaterialLink.query.order_by(MaterialLink.topic_name, MaterialLink.display_order).all()
    abele_links = ABELELink.query.order_by(ABELELink.display_order).all()
    topics = ['AREA I', 'AREA II', 'AREA III', 'Engineering Mathematics', 'PAES Standards']
    
    return render_template('admin/manage_links.html',
                         material_links=material_links,
                         abele_links=abele_links,
                         topics=topics,
                         title='Manage Links')


@admin_bp.route('/material-links/create', methods=['POST'])
@login_required
def create_material_link():
    """Create a new material link (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        topic_name = request.form.get('topic_name', '').strip()
        material_title = request.form.get('material_title', '').strip()
        link_name = request.form.get('link_name', '').strip()
        link_url = request.form.get('link_url', '').strip()
        display_order = request.form.get('display_order', 0, type=int)
        
        if not all([topic_name, material_title, link_name, link_url]):
            flash('All fields are required', 'danger')
            return redirect(url_for('admin.manage_links'))
        
        link = MaterialLink(
            topic_name=topic_name,
            material_title=material_title,
            link_name=link_name,
            link_url=link_url,
            link_type='google_drive' if 'drive' in link_url else 'youtube',
            display_order=display_order
        )
        
        db.session.add(link)
        db.session.commit()
        
        flash('Material link created successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating link: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_links'))


@admin_bp.route('/material-link/<int:link_id>/edit', methods=['POST'])
@login_required
def edit_material_link_old(link_id):
    """Edit a material link (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        link = MaterialLink.query.get_or_404(link_id)
        
        link.topic_name = request.form.get('topic_name', '').strip()
        link.material_title = request.form.get('material_title', '').strip()
        link.link_name = request.form.get('link_name', '').strip()
        link.link_url = request.form.get('link_url', '').strip()
        link.link_type = 'google_drive' if 'drive' in link.link_url else 'youtube'
        link.display_order = request.form.get('display_order', 0, type=int)
        
        db.session.commit()
        flash('Material link updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating link: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_links'))


@admin_bp.route('/material-link/<int:link_id>/delete', methods=['POST'])
@login_required
def delete_material_link(link_id):
    """Delete a material link (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        link = MaterialLink.query.get_or_404(link_id)
        db.session.delete(link)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Link deleted!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/material-link/<int:link_id>')
@login_required
def get_material_link_old_api(link_id):
    """Get material link data for editing (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        link = MaterialLink.query.get_or_404(link_id)
        return jsonify({
            'success': True,
            'link': {
                'id': link.id,
                'topic_name': link.topic_name,
                'material_title': link.material_title,
                'link_name': link.link_name,
                'link_url': link.link_url,
                'display_order': link.display_order
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== ABELE LINKS CRUD ====================

@admin_bp.route('/abele-link/<int:link_id>/edit', methods=['POST'])
@login_required
def edit_abele_link(link_id):
    """Edit an ABELE link (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        link = ABELELink.query.get_or_404(link_id)
        
        link.title = request.form.get('title', '').strip()
        link.link_url = request.form.get('link_url', '').strip()
        
        db.session.commit()
        flash('ABELE link updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating link: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_links'))


@admin_bp.route('/abele-link/<int:link_id>/toggle', methods=['POST'])
@login_required
def toggle_abele_link(link_id):
    """Toggle ABELE link active status (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        link = ABELELink.query.get_or_404(link_id)
        data = request.get_json()
        link.is_active = data.get('is_active', not link.is_active)
        db.session.commit()
        return jsonify({'success': True, 'is_active': link.is_active})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/abele-links/add-default', methods=['POST'])
@login_required
def add_default_abele_links():
    """Add default ABELE review links (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        default_links = [
            {'section_name': 'AREA I QUIZ', 'title': 'AREA I: ABELE REVIEW - QUIZ', 'display_order': 1, 'color': 'green'},
            {'section_name': 'AREA I SOLVINGS', 'title': 'AREA I: ABELE REVIEW - SOLVINGS', 'display_order': 2, 'color': 'green'},
            {'section_name': 'AREA II QUIZ', 'title': 'AREA II: ABELE REVIEW - QUIZ', 'display_order': 3, 'color': 'blue'},
            {'section_name': 'AREA II SOLVINGS', 'title': 'AREA II: ABELE REVIEW - SOLVINGS', 'display_order': 4, 'color': 'blue'},
            {'section_name': 'AREA III QUIZ', 'title': 'AREA III: ABELE REVIEW - QUIZ', 'display_order': 5, 'color': 'purple'},
            {'section_name': 'AREA III SOLVINGS', 'title': 'AREA III: ABELE REVIEW - SOLVINGS', 'display_order': 6, 'color': 'purple'},
        ]
        
        for link_data in default_links:
            existing = ABELELink.query.filter_by(section_name=link_data['section_name']).first()
            if existing:
                existing.title = link_data['title']
                existing.display_order = link_data['display_order']
                existing.color = link_data['color']
            else:
                new_link = ABELELink(
                    section_name=link_data['section_name'],
                    title=link_data['title'],
                    link_url='#',
                    display_order=link_data['display_order'],
                    color=link_data['color']
                )
                db.session.add(new_link)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Default links added!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/abele-link/<int:link_id>')
@login_required
def get_abele_link_api(link_id):
    """Get ABELE link data for editing (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        link = ABELELink.query.get_or_404(link_id)
        return jsonify({
            'success': True,
            'link': {
                'id': link.id,
                'section_name': link.section_name,
                'title': link.title,
                'link_url': link.link_url,
                'display_order': link.display_order
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
# Add this function after the imports in routes.py
def load_initial_links_from_config():
    """Load initial links from TOPIC_CONFIG into database"""
    from app.models import MaterialLink
    from app.reviewer.routes import TOPIC_CONFIG
    
    print("Loading initial links from TOPIC_CONFIG...")
    count = 0
    
    for topic_name, config in TOPIC_CONFIG.items():
        materials = config.get('materials', [])
        for material in materials:
            material_title = material.get('title', '')
            external_links = material.get('external_links', [])
            
            for link in external_links:
                link_name = link.get('name', '')
                link_url = link.get('url', '')
                
                if link_url and link_url != '#':
                    # Check if link already exists
                    existing = MaterialLink.query.filter_by(
                        topic_name=topic_name,
                        material_title=material_title,
                        link_name=link_name
                    ).first()
                    
                    if not existing:
                        # Find material_id (simple mapping based on title)
                        material_id = 0
                        # You can implement better mapping here
                        
                        new_link = MaterialLink(
                            material_id=material_id,
                            topic_name=topic_name,
                            material_title=material_title,
                            link_name=link_name,
                            link_url=link_url,
                            link_type='google_drive' if 'drive' in link_url else 'youtube',
                            display_order=0
                        )
                        db.session.add(new_link)
                        count += 1
    
    db.session.commit()
    print(f"Loaded {count} new links from TOPIC_CONFIG")

@admin_bp.route('/announcements/create', methods=['POST'])
@login_required
def create_announcement():
    """Create a new announcement with file attachments (Admin only)"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    is_pinned = request.form.get('is_pinned') == 'True'
    
    if not title or not content:
        flash('Title and content are required', 'danger')
        return redirect(url_for('admin.manage_announcements'))
    
    attachment_file = request.files.get('attachment')
    attachment_path = None
    attachment_filename = None
    attachment_size = None
    attachment_type = None
    
    if attachment_file and attachment_file.filename:
        # You need a save_file function - add it if missing
        from werkzeug.utils import secure_filename
        if allowed_file(attachment_file.filename):
            filename = secure_filename(attachment_file.filename)
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'announcements')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            attachment_file.save(file_path)
            attachment_path = f"uploads/announcements/{unique_filename}"
            attachment_filename = filename
            attachment_size = os.path.getsize(file_path)
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                attachment_type = 'image'
            elif ext == 'pdf':
                attachment_type = 'pdf'
            else:
                attachment_type = 'document'
    
    images_files = request.files.getlist('images')
    saved_images = save_multiple_images(images_files)
    images_json = json.dumps(saved_images) if saved_images else None
    
    announcement = Announcement(
        title=title,
        content=content,
        author_id=current_user.id,
        is_pinned=is_pinned,
        attachment_file=attachment_path,
        attachment_filename=attachment_filename,
        attachment_size=attachment_size,
        attachment_type=attachment_type,
        images=images_json
    )
    
    db.session.add(announcement)
    db.session.commit()
    
    # Notify all users
    all_users = User.query.filter(User.id != current_user.id).all()
    for user in all_users:
        notification = Notification(
            user_id=user.id,
            title=f"📢 New Announcement: {title[:50]}",
            message=f"{content[:100]}..." if len(content) > 100 else content,
            notification_type='announcement',
            related_id=announcement.id,
            related_type='announcement',
            icon="fas fa-bullhorn",
            action_url=url_for('main.dashboard'),
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
    
    db.session.commit()
    
    flash('Announcement posted successfully!', 'success')
    return redirect(url_for('admin.manage_announcements'))


@admin_bp.route('/announcements/<int:announcement_id>/edit', methods=['POST'])
@login_required
def edit_announcement(announcement_id):
    """Edit an existing announcement (Admin only)"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.dashboard'))
    
    announcement = Announcement.query.get_or_404(announcement_id)
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    is_pinned = request.form.get('is_pinned') == 'True'
    
    if not title or not content:
        flash('Title and content are required', 'danger')
        return redirect(url_for('admin.manage_announcements'))
    
    # Handle new attachment
    attachment_file = request.files.get('attachment')
    if attachment_file and attachment_file.filename:
        if announcement.attachment_file:
            old_path = os.path.join(current_app.root_path, 'static', announcement.attachment_file)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        if allowed_file(attachment_file.filename):
            filename = secure_filename(attachment_file.filename)
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'announcements')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            attachment_file.save(file_path)
            announcement.attachment_file = f"uploads/announcements/{unique_filename}"
            announcement.attachment_filename = filename
            announcement.attachment_size = os.path.getsize(file_path)
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                announcement.attachment_type = 'image'
            elif ext == 'pdf':
                announcement.attachment_type = 'pdf'
            else:
                announcement.attachment_type = 'document'
    
    # Handle new images
    images_files = request.files.getlist('images')
    if images_files and any(f.filename for f in images_files):
        new_images = save_multiple_images(images_files)
        if new_images:
            existing_images = announcement.get_images_list()
            existing_images.extend(new_images)
            announcement.images = json.dumps(existing_images) if existing_images else None
    
    announcement.title = title
    announcement.content = content
    announcement.is_pinned = is_pinned
    announcement.updated_at = datetime.utcnow()
    
    db.session.commit()
    flash('Announcement updated successfully!', 'success')
    return redirect(url_for('admin.manage_announcements'))


@admin_bp.route('/api/announcement/<int:announcement_id>')
@login_required
def get_announcement_api(announcement_id):
    """Get single announcement data for editing (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        
        size_display = ''
        if announcement.attachment_size:
            size = announcement.attachment_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    size_display = f"{size:.1f} {unit}"
                    break
                size /= 1024.0
        
        return jsonify({
            'success': True,
            'announcement': {
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'is_pinned': announcement.is_pinned,
                'attachment_file': announcement.attachment_file,
                'attachment_filename': announcement.attachment_filename,
                'attachment_size_display': size_display,
                'attachment_type': announcement.attachment_type,
                'images': announcement.get_images_list()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/announcements/<int:announcement_id>/delete', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    """Delete an announcement (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        
        # Delete attachment file if exists
        if announcement.attachment_file:
            file_path = os.path.join(current_app.root_path, 'static', announcement.attachment_file)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete image files if exists
        for img in announcement.get_images_list():
            img_path = os.path.join(current_app.root_path, 'static', img)
            if os.path.exists(img_path):
                os.remove(img_path)
        
        db.session.delete(announcement)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Announcement deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/announcements/<int:announcement_id>/delete-image', methods=['POST'])
@login_required
def delete_announcement_image(announcement_id):
    """Delete a specific image from announcement (Admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    image_path = data.get('image_path')
    
    if not image_path:
        return jsonify({'success': False, 'message': 'No image specified'}), 400
    
    announcement = Announcement.query.get_or_404(announcement_id)
    images = announcement.get_images_list()
    
    if image_path in images:
        file_path = os.path.join(current_app.root_path, 'static', image_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        images.remove(image_path)
        announcement.images = json.dumps(images) if images else None
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Image deleted'})
    
    return jsonify({'success': False, 'message': 'Image not found'}), 404