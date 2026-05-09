# app/community/helpers.py
from app import db
from app.models import Post, HiddenPost, SavedPost, PostInterest, SnoozedPost
from flask_login import current_user
from datetime import datetime, timedelta

def get_user_post_interactions(post_id):
    """Get all user interactions for a post"""
    return {
        'hidden': current_user.has_hidden_post(post_id),
        'saved': current_user.has_saved_post(post_id),
        'snoozed': current_user.has_snoozed_post(post_id),
        'interest': current_user.get_post_interest(post_id)
    }

def filter_snoozed_posts(posts_query):
    """Filter out snoozed posts for current user"""
    snoozed_posts = SnoozedPost.query.filter_by(
        user_id=current_user.id
    ).filter(
        SnoozedPost.snooze_until > datetime.utcnow()
    ).all()
    
    snoozed_post_ids = [sp.post_id for sp in snoozed_posts]
    
    if snoozed_post_ids:
        return posts_query.filter(Post.id.notin_(snoozed_post_ids))
    
    return posts_query

def filter_hidden_posts(posts_query):
    """Filter out hidden posts for current user"""
    hidden_posts = HiddenPost.query.filter_by(user_id=current_user.id).all()
    hidden_post_ids = [hp.post_id for hp in hidden_posts]
    
    if hidden_post_ids:
        return posts_query.filter(Post.id.notin_(hidden_post_ids))
    
    return posts_query