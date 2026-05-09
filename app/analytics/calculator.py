# app/analytics/calculator.py - COMPLETE FIXED VERSION
from app import db
from app.models import QuizResult, Topic, Question
from datetime import datetime, timedelta
from sqlalchemy import func

def get_user_performance_data(user_id, days=7):
    """
    Centralized function to calculate all performance metrics consistently.
    Returns a standardized dictionary with all performance data.
    """
    try:
        # Get date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all quiz results for the user
        quiz_results = QuizResult.query.filter(
            QuizResult.user_id == user_id,
            QuizResult.completed_at.isnot(None)
        ).all()
        
        if not quiz_results:
            return _get_empty_performance_data(days)
        
        # Calculate overall score (all time)
        overall_score = _calculate_overall_score(quiz_results)
        
        # Calculate daily averages for the specified period
        daily_averages = _calculate_daily_averages(quiz_results, start_date, end_date)
        
        # Calculate topic mastery
        topic_mastery = _calculate_topic_mastery(quiz_results)
        
        # Calculate topic trends for categories
        topic_trends = _calculate_topic_trends_fixed(user_id, start_date, end_date, days)
        
        # Format dates for display
        date_range_dates = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_range_dates.append(current_date)
            current_date += timedelta(days=1)
        
        dates_formatted = [date.strftime('%m/%d') for date in date_range_dates]
        
        return {
            'overall_score': overall_score,
            'date_range': {
                'start': start_date.date(),
                'end': end_date.date()
            },
            'dates': dates_formatted,
            'daily_averages': daily_averages,
            'topic_mastery': topic_mastery,
            'topic_trends': topic_trends
        }
        
    except Exception as e:
        print(f"Error in get_user_performance_data: {e}")
        import traceback
        traceback.print_exc()
        return _get_empty_performance_data(days)

def _get_empty_performance_data(days):
    """Return empty performance data structure"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    date_range_dates = []
    current_date = start_date.date()
    while current_date <= end_date.date():
        date_range_dates.append(current_date)
        current_date += timedelta(days=1)
    
    dates_formatted = [date.strftime('%m/%d') for date in date_range_dates]
    
    return {
        'overall_score': 0,
        'date_range': {
            'start': start_date.date(),
            'end': end_date.date()
        },
        'dates': dates_formatted,
        'daily_averages': [0] * len(dates_formatted),
        'topic_mastery': [],
        'topic_trends': {
            'AREA I': [0] * len(dates_formatted),
            'AREA II': [0] * len(dates_formatted),
            'AREA III': [0] * len(dates_formatted),
            'Engineering Mathematics': [0] * len(dates_formatted),
            'PAES Standards': [0] * len(dates_formatted)
        }
    }

def _calculate_overall_score(quiz_results):
    """Calculate overall average score from all quiz results"""
    if not quiz_results:
        return 0
    
    total_score = sum(result.score for result in quiz_results)
    return round(total_score / len(quiz_results), 2)

def _calculate_daily_averages(quiz_results, start_date, end_date):
    """Calculate daily average scores for the date range"""
    date_range = []
    current_date = start_date.date()
    while current_date <= end_date.date():
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    daily_scores = {date: [] for date in date_range}
    
    for result in quiz_results:
        if result.completed_at:
            result_date = result.completed_at.date()
            if result_date in daily_scores:
                daily_scores[result_date].append(result.score)
    
    daily_averages = []
    for date in date_range:
        scores = daily_scores[date]
        if scores:
            daily_averages.append(round(sum(scores) / len(scores), 2))
        else:
            daily_averages.append(0)
    
    return daily_averages

def _calculate_topic_mastery(quiz_results):
    """Calculate average score for each topic"""
    topic_scores = {}
    
    for result in quiz_results:
        topic_id = result.topic_id
        if topic_id not in topic_scores:
            topic_scores[topic_id] = {
                'scores': [],
                'count': 0,
                'topic_name': result.topic.name if result.topic else f"Topic {topic_id}"
            }
        topic_scores[topic_id]['scores'].append(result.score)
        topic_scores[topic_id]['count'] += 1
    
    mastery_data = []
    for topic_id, data in topic_scores.items():
        avg_score = round(sum(data['scores']) / len(data['scores']), 2)
        
        if avg_score >= 90:
            level = "Excellent"
            color_class = "bg-green-600"
        elif avg_score >= 75:
            level = "Good"
            color_class = "bg-blue-600"
        elif avg_score >= 60:
            level = "Average"
            color_class = "bg-yellow-500"
        elif avg_score >= 40:
            level = "Needs Improvement"
            color_class = "bg-orange-500"
        else:
            level = "Poor"
            color_class = "bg-red-600"
        
        mastery_data.append({
            'id': topic_id,
            'name': data['topic_name'],
            'score': avg_score,
            'quiz_count': data['count'],
            'level': level,
            'color_class': color_class
        })
    
    return mastery_data

def _calculate_topic_trends_fixed(user_id, start_date, end_date, days=7):
    """
    FIXED: Calculate daily averages for the 5 main display categories
    This queries the database directly using SQL for accurate results
    """
    # Create date range
    date_range = []
    current_date = start_date.date()
    while current_date <= end_date.date():
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    # Define category mapping based on topic names
    category_keywords = {
        'AREA I': ['farm machinery', 'agricultural machinery', 'farm equipment', 'tractor', 'power engineering', 'mechanization', 'area i'],
        'AREA II': ['soil', 'water', 'soil and water', 'conservation', 'irrigation', 'drainage', 'hydrology', 'aquaculture', 'area ii'],
        'AREA III': ['post-harvest', 'post harvest', 'processing', 'storage', 'drying', 'milling', 'bioprocess', 'food engineering', 'structures', 'electrification', 'area iii'],
        'Engineering Mathematics': ['math', 'mathematics', 'engineering math', 'calculus', 'algebra', 'maths', 'statistics', 'probability'],
        'PAES Standards': ['paes', 'standard', 'code', 'amtec', 'specification', 'regulation']
    }
    
    # Initialize result dictionary with zeros
    result = {category: [0] * len(date_range) for category in category_keywords.keys()}
    
    # Get all topics from database
    all_topics = Topic.query.all()
    
    # Build topic_id to category mapping
    topic_category_map = {}
    for topic in all_topics:
        topic_name_lower = topic.name.lower()
        mapped_category = None
        
        for category, keywords in category_keywords.items():
            if any(keyword in topic_name_lower for keyword in keywords):
                mapped_category = category
                break
        
        if mapped_category:
            topic_category_map[topic.id] = mapped_category
        else:
            # Default fallback based on name patterns
            if 'machinery' in topic_name_lower or 'equipment' in topic_name_lower or 'tractor' in topic_name_lower:
                topic_category_map[topic.id] = 'AREA I'
            elif 'soil' in topic_name_lower or 'water' in topic_name_lower or 'irrigation' in topic_name_lower:
                topic_category_map[topic.id] = 'AREA II'
            elif 'post' in topic_name_lower or 'harvest' in topic_name_lower or 'storage' in topic_name_lower or 'processing' in topic_name_lower:
                topic_category_map[topic.id] = 'AREA III'
            elif 'math' in topic_name_lower or 'calculus' in topic_name_lower or 'algebra' in topic_name_lower:
                topic_category_map[topic.id] = 'Engineering Mathematics'
            elif 'paes' in topic_name_lower or 'standard' in topic_name_lower:
                topic_category_map[topic.id] = 'PAES Standards'
            else:
                # Default to Engineering Mathematics for unmapped topics
                topic_category_map[topic.id] = 'Engineering Mathematics'
    
    # Get all quiz results within date range
    quiz_results = QuizResult.query.filter(
        QuizResult.user_id == user_id,
        QuizResult.completed_at.isnot(None),
        QuizResult.completed_at >= start_date,
        QuizResult.completed_at <= end_date
    ).all()
    
    # Create date to index mapping
    date_index_map = {date_range[i]: i for i in range(len(date_range))}
    
    # Create a dictionary to store scores by category and date
    category_date_scores = {category: {date: [] for date in date_range} for category in category_keywords.keys()}
    
    # Process each quiz result
    for quiz_result in quiz_results:
        result_date = quiz_result.completed_at.date()
        if result_date not in date_index_map:
            continue
        
        topic_id = quiz_result.topic_id
        category = topic_category_map.get(topic_id)
        
        if category and category in category_date_scores:
            # Store the score for averaging later
            category_date_scores[category][result_date].append(quiz_result.score)
    
    # Calculate averages for each category and date
    for category in result.keys():
        for i, date_obj in enumerate(date_range):
            scores = category_date_scores[category][date_obj]
            if scores:
                result[category][i] = round(sum(scores) / len(scores), 2)
            else:
                result[category][i] = 0
    
    print(f"DEBUG - Topic Trends Calculated: {result}")
    return result

def get_weak_areas(user_id, threshold=60):
    """Identify topics where user scores below threshold"""
    quiz_results = QuizResult.query.filter_by(user_id=user_id).all()
    
    if not quiz_results:
        return []
    
    topic_scores = {}
    for result in quiz_results:
        topic_id = result.topic_id
        if topic_id not in topic_scores:
            topic_scores[topic_id] = {'scores': [], 'name': result.topic.name if result.topic else f"Topic {topic_id}"}
        topic_scores[topic_id]['scores'].append(result.score)
    
    weak_areas = []
    for topic_id, data in topic_scores.items():
        avg_score = sum(data['scores']) / len(data['scores'])
        if avg_score < threshold:
            weak_areas.append({
                'topic_id': topic_id,
                'topic_name': data['name'],
                'avg_score': round(avg_score, 2),
                'quiz_count': len(data['scores'])
            })
    
    return sorted(weak_areas, key=lambda x: x['avg_score'])

def get_recommendations(user_id):
    """Generate study recommendations based on performance"""
    weak_areas = get_weak_areas(user_id, 60)
    
    recommendations = []
    
    if weak_areas:
        recommendations.append({
            'type': 'weak_areas',
            'title': 'Focus on Weak Topics',
            'message': f"You should focus more on {weak_areas[0]['topic_name']}.",
            'icon': 'fas fa-exclamation-triangle',
            'color': 'orange'
        })
    
    # Check quiz frequency
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_quizzes = QuizResult.query.filter(
        QuizResult.user_id == user_id,
        QuizResult.completed_at >= thirty_days_ago
    ).count()
    
    if recent_quizzes < 5:
        recommendations.append({
            'type': 'consistency',
            'title': 'Build Consistency',
            'message': 'Take more quizzes to track your progress effectively.',
            'icon': 'fas fa-calendar-alt',
            'color': 'blue'
        })
    
    if not recommendations:
        recommendations.append({
            'type': 'good_job',
            'title': 'Great Progress!',
            'message': 'Keep up the good work and continue practicing.',
            'icon': 'fas fa-trophy',
            'color': 'green'
        })
    
    return recommendations