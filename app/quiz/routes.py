# app/quiz/routes.py - COMPLETE WITH ACHIEVEMENT CHECKING
from flask import render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Topic, Question, QuizResult, Notification
from app.quiz.engine import generate_quiz, calculate_score, generate_random_quiz
from app.quiz.forms import QuizAnswerForm
from app.quiz import quiz_bp
import json
from datetime import datetime

@quiz_bp.route('/')
@login_required
def quiz_home():
    topics = Topic.query.all()
    return render_template('quiz/start_quiz.html', title='Take Quiz', topics=topics)

@quiz_bp.route('/start', methods=['POST'])
@login_required
def start_quiz():
    topic_id = request.form.get('topic_id')
    num_questions = int(request.form.get('num_questions', 10))
    is_random = request.form.get('is_random') == 'true'
    is_timed = request.form.get('is_timed') == 'true'
    
    if is_random:
        questions = generate_random_quiz(num_questions)
    else:
        questions = generate_quiz(topic_id, num_questions)
    
    if not questions:
        flash('No questions available for this topic', 'warning')
        return redirect(url_for('quiz.quiz_home'))
    
    # Store quiz data in session
    session['quiz_questions'] = [q.id for q in questions]
    session['quiz_answers'] = {}
    session['quiz_topic_id'] = topic_id if not is_random else None
    session['quiz_is_random'] = is_random
    session['quiz_is_timed'] = is_timed
    session['quiz_start_time'] = datetime.now().isoformat() if is_timed else None
    session['quiz_total_questions'] = len(questions)
    session['quiz_current_question'] = 1
    
    return redirect(url_for('quiz.take_quiz', question_num=1))

@quiz_bp.route('/take/<int:question_num>')
@login_required
def take_quiz(question_num):
    # Check if quiz session exists
    if 'quiz_questions' not in session or not session['quiz_questions']:
        flash('No active quiz session. Please start a new quiz.', 'info')
        return redirect(url_for('quiz.quiz_home'))
    
    total_questions = len(session['quiz_questions'])
    
    # Validate question number
    if question_num < 1 or question_num > total_questions:
        flash('Invalid question number', 'error')
        return redirect(url_for('quiz.quiz_home'))
    
    # Update current question in session
    session['quiz_current_question'] = question_num
    session.modified = True
    
    # Get question from database
    question_id = session['quiz_questions'][question_num - 1]
    question = Question.query.get_or_404(question_id)
    
    # Get the user's answer if already answered
    user_answer = session['quiz_answers'].get(str(question_id))
    
    # Create form and pre-populate data
    form = QuizAnswerForm()
    form.question_id.data = question_id
    form.question_num.data = question_num
    form.total_questions.data = total_questions
    
    # Pre-select the answer if user already answered
    if user_answer:
        form.answer.data = user_answer
    
    # Calculate time remaining for timed quizzes
    time_remaining = None
    if session.get('quiz_is_timed') and session.get('quiz_start_time'):
        time_per_question = 60  # seconds per question
        elapsed = (datetime.now() - datetime.fromisoformat(session['quiz_start_time'])).total_seconds()
        total_time = total_questions * time_per_question
        time_remaining = max(0, total_time - elapsed)
    
    return render_template('quiz/take_quiz.html',
                         title='Quiz',
                         question=question,
                         question_num=question_num,
                         total_questions=total_questions,
                         user_answer=user_answer,
                         time_remaining=time_remaining,
                         form=form)

@quiz_bp.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    form = QuizAnswerForm()
    
    # Check if quiz session exists
    if 'quiz_questions' not in session or 'quiz_answers' not in session:
        flash('No active quiz session', 'error')
        return redirect(url_for('quiz.quiz_home'))
    
    if form.validate_on_submit():
        question_id = form.question_id.data
        answer = form.answer.data
        question_num = int(form.question_num.data)
        time_taken = form.time_taken.data or 60
        
        # Store answer in session
        session['quiz_answers'][question_id] = answer
        session.modified = True
        
        total_questions = len(session['quiz_questions'])
        
        # Redirect to next question or results
        if question_num < total_questions:
            return redirect(url_for('quiz.take_quiz', question_num=question_num + 1))
        else:
            return redirect(url_for('quiz.submit_quiz'))
    else:
        # Form validation failed (including CSRF)
        flash('Please select an answer', 'error')
        question_num = int(request.form.get('question_num', 1))
        return redirect(url_for('quiz.take_quiz', question_num=question_num))

@quiz_bp.route('/submit')
@login_required
def submit_quiz():
    # Check if quiz session exists
    if 'quiz_questions' not in session or 'quiz_answers' not in session:
        flash('No active quiz session', 'error')
        return redirect(url_for('quiz.quiz_home'))
    
    # Get questions from database
    question_ids = session['quiz_questions']
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    
    # Calculate score
    score, correct, total = calculate_score(questions, session['quiz_answers'])
    
    # Calculate percentage
    percentage = (correct / total) * 100 if total > 0 else 0
    
    # Determine topic ID
    topic_id = session.get('quiz_topic_id')
    topic_name = "Random Quiz"
    if topic_id is None and questions:
        topic_id = questions[0].topic_id
        topic = Topic.query.get(topic_id)
        topic_name = topic.name if topic else "Quiz"
    elif topic_id:
        topic = Topic.query.get(topic_id)
        topic_name = topic.name if topic else "Quiz"
    
    # Calculate total time taken if it was a timed quiz
    time_taken = None
    if session.get('quiz_is_timed') and session.get('quiz_start_time'):
        start_time = datetime.fromisoformat(session['quiz_start_time'])
        time_taken = int((datetime.now() - start_time).total_seconds())
    
    # DEBUG: Print values before saving
    print(f"DEBUG - Saving quiz result:")
    print(f"  user_id: {current_user.id}")
    print(f"  topic_id: {topic_id}")
    print(f"  score: {score}")
    print(f"  total_questions: {total}")
    print(f"  percentage: {percentage}")
    print(f"  time_taken: {time_taken}")
    
    # Save quiz result
    quiz_result = QuizResult(
        user_id=current_user.id,
        topic_id=topic_id,
        score=score,
        total_questions=total,
        percentage=percentage,
        time_taken=time_taken,
        completed_at=datetime.now()
    )
    
    db.session.add(quiz_result)
    db.session.commit()
    
    print(f"DEBUG - Quiz result saved with ID: {quiz_result.id}")
    
    # ========== CHECK ACHIEVEMENTS AFTER QUIZ COMPLETION ==========
    try:
        from app.achievements.routes import check_achievements
        check_achievements()
        print("DEBUG - Achievements checked after quiz completion")
    except Exception as e:
        print(f"DEBUG - Error checking achievements: {e}")
    # ========== END ACHIEVEMENT CHECK ==========
    
    # ========== CREATE NOTIFICATION FOR QUIZ COMPLETION ==========
    # Determine notification style based on performance
    if percentage >= 90:
        title = "🎉 Excellent! Perfect Score!"
        icon = "fas fa-trophy"
        message = f"You scored {percentage:.1f}% on {topic_name} - Outstanding!"
    elif percentage >= 75:
        title = "✅ Great Job! Quiz Completed"
        icon = "fas fa-check-circle"
        message = f"You scored {percentage:.1f}% on {topic_name} - Well done!"
    elif percentage >= 60:
        title = "📝 Quiz Completed"
        icon = "fas fa-clipboard-list"
        message = f"You scored {percentage:.1f}% on {topic_name} - Good effort!"
    else:
        title = "📚 Keep Practicing!"
        icon = "fas fa-book-open"
        message = f"You scored {percentage:.1f}% on {topic_name} - Review and try again!"
    
    # Check if this is a personal best for this topic
    previous_best = QuizResult.query.filter(
        QuizResult.user_id == current_user.id,
        QuizResult.topic_id == topic_id,
        QuizResult.id != quiz_result.id
    ).order_by(QuizResult.percentage.desc()).first()
    
    if previous_best and percentage > previous_best.percentage:
        title = "🏆 New Personal Best!"
        message = f"New high score! {percentage:.1f}% on {topic_name} (Previous: {previous_best.percentage:.1f}%)"
        icon = "fas fa-chart-line"
    
    notification = Notification(
        user_id=current_user.id,
        title=title,
        message=message,
        notification_type='quiz_complete',
        related_id=quiz_result.id,
        related_type='quiz_result',
        icon=icon,
        action_url=url_for('quiz.review_quiz'),
        created_at=datetime.utcnow()
    )
    db.session.add(notification)
    db.session.commit()
    print(f"DEBUG - Quiz notification created: {title}")
    # ========== END NOTIFICATION ==========
    
    # Store questions and answers for results page
    session['quiz_results_questions'] = [q.id for q in questions]
    session['quiz_results_answers'] = session['quiz_answers'].copy()
    
    # Clear quiz session but keep results for display
    session_keys = ['quiz_questions', 'quiz_answers', 'quiz_topic_id', 
                   'quiz_is_random', 'quiz_is_timed', 'quiz_start_time',
                   'quiz_total_questions', 'quiz_current_question']
    for key in session_keys:
        session.pop(key, None)
    
    return render_template('quiz/result.html',
                         title='Quiz Results',
                         score=score,
                         correct=correct,
                         total=total,
                         percentage=percentage,
                         questions=questions,
                         user_answers=session.get('quiz_results_answers', {}))

@quiz_bp.route('/review')
@login_required
def review_quiz():
    """Review quiz results with correct/incorrect answers"""
    if 'quiz_results_questions' not in session:
        flash('No quiz results to review', 'info')
        return redirect(url_for('main.dashboard'))
    
    question_ids = session['quiz_results_questions']
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    user_answers = session.get('quiz_results_answers', {})
    
    return render_template('quiz/review.html',
                         title='Review Quiz',
                         questions=questions,
                         user_answers=user_answers)

@quiz_bp.route('/categories')
@login_required
def quiz_categories():
    """Display quiz categories/topics"""
    topics = Topic.query.all()
    return render_template('quiz/start_quiz.html', title='Quiz Categories', topics=topics)

@quiz_bp.route('/start-quiz')
@login_required
def start_quiz_page():
    """GET route for the start quiz page - shows topic selection"""
    topics = Topic.query.all()
    return render_template('quiz/start_quiz.html', title='Take Quiz', topics=topics)