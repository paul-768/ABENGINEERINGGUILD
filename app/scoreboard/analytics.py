# app/scoreboard/analytics.py - COMPLETE CORRECTED VERSION WITH PROFILE PICTURES
from app import db
from app.models import User, QuizResult, Topic
from datetime import datetime, timedelta
from sqlalchemy import func
import json

def get_scoreboard_data(start_date=None):
    """
    Get scoreboard data - ranked by CUSTOM FORMULA:
    ((total_score / total_questions) + accuracy) / 2
    """
    try:
        query = QuizResult.query.filter(QuizResult.completed_at.isnot(None))
        
        if start_date:
            query = query.filter(QuizResult.completed_at >= start_date)
        
        results = query.all()
        
        user_scores = {}
        for result in results:
            user_id = result.user_id
            if user_id not in user_scores:
                user = User.query.get(user_id)
                user_scores[user_id] = {
                    'user_id': user_id,
                    'name': user.name if user else f"User {user_id}",
                    'profile_picture': user.profile_picture if user else 'default_profile.png',
                    'total_quizzes': 0,
                    'total_questions': 0,
                    'total_correct': 0,
                    'total_score_sum': 0,
                    'scores': []
                }
            
            user_scores[user_id]['total_quizzes'] += 1
            correct_count = (result.score / 100.0) * result.total_questions
            user_scores[user_id]['total_questions'] += result.total_questions
            user_scores[user_id]['total_correct'] += correct_count
            user_scores[user_id]['total_score_sum'] += result.score
            user_scores[user_id]['scores'].append(result.score)
        
        scoreboard_data = []
        for user_id, data in user_scores.items():
            accuracy = (data['total_correct'] / data['total_questions'] * 100) if data['total_questions'] > 0 else 0
            average_score_percent = (data['total_score_sum'] / data['total_quizzes']) if data['total_quizzes'] > 0 else 0
            rank_score = (average_score_percent + accuracy) / 2
            
            scoreboard_data.append({
                'user_id': user_id,
                'name': data['name'],
                'profile_picture': data['profile_picture'],
                'quizzes_taken': data['total_quizzes'],
                'total_questions': data['total_questions'],
                'total_correct': round(data['total_correct'], 0),
                'accuracy': round(accuracy, 2),
                'average_score': round(average_score_percent, 2),
                'rank_score': round(rank_score, 2)
            })
        
        scoreboard_data.sort(key=lambda x: x['rank_score'], reverse=True)
        return scoreboard_data
    except Exception as e:
        print(f"Error in get_scoreboard_data: {e}")
        return []


def get_top_scorers_data(start_date=None):
    """Get Top 5 Overall Scorers with profile pictures"""
    try:
        query = QuizResult.query.filter(QuizResult.completed_at.isnot(None))
        
        if start_date:
            query = query.filter(QuizResult.completed_at >= start_date)
        
        results = query.all()
        
        user_scores = {}
        for result in results:
            user_id = result.user_id
            if user_id not in user_scores:
                user = User.query.get(user_id)
                user_scores[user_id] = {
                    'user_id': user_id,
                    'name': user.name if user else f"User {user_id}",
                    'profile_picture': user.profile_picture if user else 'default_profile.png',
                    'total_quizzes': 0,
                    'total_questions': 0,
                    'total_correct': 0,
                    'total_score_sum': 0,
                    'scores': []
                }
            
            user_scores[user_id]['total_quizzes'] += 1
            correct_count = (result.score / 100.0) * result.total_questions
            user_scores[user_id]['total_questions'] += result.total_questions
            user_scores[user_id]['total_correct'] += correct_count
            user_scores[user_id]['total_score_sum'] += result.score
            user_scores[user_id]['scores'].append(result.score)
        
        top_scorers_data = []
        for user_id, data in user_scores.items():
            overall_score_percent = (data['total_score_sum'] / data['total_quizzes']) if data['total_quizzes'] > 0 else 0
            
            top_scorers_data.append({
                'user_id': user_id,
                'name': data['name'],
                'profile_picture': data['profile_picture'],
                'overall_score_percent': round(overall_score_percent, 2),
                'total_correct': round(data['total_correct'], 0),
                'total_questions': data['total_questions'],
                'quizzes_taken': data['total_quizzes']
            })
        
        top_scorers_data.sort(key=lambda x: x['total_correct'], reverse=True)
        return top_scorers_data[:5]
    except Exception as e:
        print(f"Error in get_top_scorers_data: {e}")
        return []


def get_user_rank(user_id, start_date=None):
    """Get user's rank based on custom formula"""
    try:
        scoreboard_data = get_scoreboard_data(start_date)
        for rank, student in enumerate(scoreboard_data, 1):
            if student['user_id'] == user_id:
                return rank
        return None
    except Exception as e:
        print(f"Error in get_user_rank: {e}")
        return None


def get_user_progress(user_id, days=7):
    """Get user's progress over time - includes all 7 days"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Create date range for ALL days
        date_range = []
        current_date = start_date.date()
        end_date_calc = end_date.date()
        
        while current_date <= end_date_calc:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        dates_formatted = [d.strftime('%m/%d') for d in date_range]
        
        # Get quiz results within date range
        daily_scores = db.session.query(
            func.date(QuizResult.completed_at).label('date'),
            func.avg(QuizResult.score).label('avg_score')
        ).filter(
            QuizResult.user_id == user_id,
            QuizResult.completed_at.isnot(None),
            QuizResult.completed_at >= start_date
        ).group_by(
            func.date(QuizResult.completed_at)
        ).order_by(
            func.date(QuizResult.completed_at)
        ).all()
        
        # Create dictionary of date -> average score
        score_dict = {}
        for row in daily_scores:
            if row.date:
                score_dict[str(row.date)] = round(float(row.avg_score), 2)
        
        # Build daily averages for ALL dates in range
        daily_averages = []
        for date_obj in date_range:
            date_str = str(date_obj)
            if date_str in score_dict:
                daily_averages.append(score_dict[date_str])
            else:
                daily_averages.append(0)
        
        print(f"\n[DEBUG] User {user_id} Progress Data:")
        print(f"  Date Range: {start_date.date()} to {end_date.date()} ({len(date_range)} days)")
        print(f"  Quiz Results Found: {len(daily_scores)}")
        print(f"  Daily Averages: {daily_averages}")
        print(f"  Dates: {dates_formatted}\n")
        
        return {
            'dates': dates_formatted,
            'averages': daily_averages
        }
    except Exception as e:
        print(f"Error in get_user_progress: {e}")
        return {'dates': [], 'averages': []}


def get_topic_mastery(user_id):
    """Get topic-wise mastery scores"""
    try:
        topics = Topic.query.all()
        topic_performance = []
        
        for topic in topics:
            results = QuizResult.query.filter_by(
                user_id=user_id,
                topic_id=topic.id
            ).all()
            
            if results:
                avg_score = sum(r.score for r in results) / len(results)
                quiz_count = len(results)
            else:
                avg_score = 0
                quiz_count = 0
            
            # Get icon and color from topic if available
            icon = getattr(topic, 'icon', 'fas fa-book')
            color = getattr(topic, 'color', '#4CAF50')
            
            topic_performance.append({
                'id': topic.id,
                'name': topic.name,
                'score': round(avg_score, 2),
                'quiz_count': quiz_count,
                'icon': icon,
                'color': color
            })
        
        return topic_performance
    except Exception as e:
        print(f"Error in get_topic_mastery: {e}")
        return []


def get_performance_grid_data(user_id):
    """Get 10x10 performance grid"""
    try:
        results = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.completed_at).all()
        
        if not results:
            return {'grid': [[0 for _ in range(10)] for _ in range(10)], 'total_cells': 0, 'filled_cells': 0}
        
        grid = [[0 for _ in range(10)] for _ in range(10)]
        recent_results = results[-100:] if len(results) > 100 else results
        
        for i, result in enumerate(recent_results):
            row = i // 10
            col = i % 10
            if row < 10 and col < 10:
                level = min(9, int(result.score / 10))
                grid[row][col] = level + 1
        
        return {
            'grid': grid,
            'total_cells': 100,
            'filled_cells': len(recent_results)
        }
    except Exception as e:
        print(f"Error in get_performance_grid_data: {e}")
        return {'grid': [[0 for _ in range(10)] for _ in range(10)], 'total_cells': 0, 'filled_cells': 0}


def get_user_quiz_stats(user_id):
    """Get comprehensive quiz statistics for a user"""
    try:
        results = QuizResult.query.filter_by(user_id=user_id).all()
        
        if not results:
            return {
                'total_quizzes': 0,
                'total_questions': 0,
                'total_correct': 0,
                'average_score': 0,
                'accuracy': 0,
                'best_score': 0,
                'worst_score': 0,
                'recent_scores': []
            }
        
        total_quizzes = len(results)
        total_questions = sum(r.total_questions for r in results)
        total_correct = sum((r.score / 100.0) * r.total_questions for r in results)
        average_score = sum(r.score for r in results) / total_quizzes
        accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        best_score = max(r.score for r in results)
        worst_score = min(r.score for r in results)
        
        # Get recent scores (last 5)
        recent_scores = sorted(results, key=lambda x: x.completed_at, reverse=True)[:5]
        recent_scores_data = [{'score': r.score, 'date': r.completed_at.strftime('%b %d')} for r in recent_scores]
        
        return {
            'total_quizzes': total_quizzes,
            'total_questions': total_questions,
            'total_correct': round(total_correct, 0),
            'average_score': round(average_score, 2),
            'accuracy': round(accuracy, 2),
            'best_score': round(best_score, 2),
            'worst_score': round(worst_score, 2),
            'recent_scores': recent_scores_data
        }
    except Exception as e:
        print(f"Error in get_user_quiz_stats: {e}")
        return {
            'total_quizzes': 0,
            'total_questions': 0,
            'total_correct': 0,
            'average_score': 0,
            'accuracy': 0,
            'best_score': 0,
            'worst_score': 0,
            'recent_scores': []
        }