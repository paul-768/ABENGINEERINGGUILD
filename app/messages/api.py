# app/messages/api.py - ADDITIONAL API ENDPOINTS
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Conversation, Message, Friendship, FriendRequest
from datetime import datetime
from sqlalchemy import or_, and_

from app.messages import messages_bp

@messages_bp.route('/api/check_conversation/<int:user_id>', methods=['GET'])
@login_required
def check_conversation(user_id):
    """Check if conversation exists with user"""
    try:
        other_user = User.query.get_or_404(user_id)
        
        if other_user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot message yourself'}), 400
        
        # Check if conversation exists
        conversation = Conversation.query.filter(
            or_(
                and_(Conversation.user1_id == current_user.id, Conversation.user2_id == user_id),
                and_(Conversation.user1_id == user_id, Conversation.user2_id == current_user.id)
            )
        ).first()
        
        if conversation:
            return jsonify({
                'success': True,
                'exists': True,
                'conversation_id': conversation.id
            })
        else:
            return jsonify({
                'success': True,
                'exists': False,
                'user': {
                    'id': other_user.id,
                    'name': other_user.name,
                    'profile_picture': other_user.profile_picture or 'default_profile.png',
                    'is_online': other_user.is_online()
                }
            })
    except Exception as e:
        current_app.logger.error(f"Error checking conversation: {e}")
        return jsonify({'success': False, 'message': 'Error checking conversation'}), 500

@messages_bp.route('/api/create_conversation', methods=['POST'])
@login_required
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        other_user = User.query.get(user_id)
        if not other_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if other_user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot message yourself'}), 400
        
        # Check if conversation already exists
        existing_conv = Conversation.query.filter(
            or_(
                and_(Conversation.user1_id == current_user.id, Conversation.user2_id == user_id),
                and_(Conversation.user1_id == user_id, Conversation.user2_id == current_user.id)
            )
        ).first()
        
        if existing_conv:
            return jsonify({
                'success': True,
                'conversation_id': existing_conv.id,
                'message': 'Conversation already exists'
            })
        
        # Create new conversation
        conversation = Conversation(
            user1_id=current_user.id,
            user2_id=user_id,
            last_message_at=datetime.utcnow()
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        # Create a welcome message
        welcome_message = Message(
            content=f"Hello! You've started a conversation with {other_user.name}.",
            sender_id=current_user.id,
            receiver_id=user_id,
            conversation_id=conversation.id,
            delivered_at=datetime.utcnow()
        )
        
        db.session.add(welcome_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation_id': conversation.id,
            'message': 'Conversation created successfully'
        })
    except Exception as e:
        current_app.logger.error(f"Error creating conversation: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error creating conversation'}), 500

@messages_bp.route('/api/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    """Delete a message (soft delete)"""
    try:
        message = Message.query.get_or_404(message_id)
        
        if message.sender_id != current_user.id:
            return jsonify({'success': False, 'message': 'You can only delete your own messages'}), 403
        
        # Soft delete by marking as deleted
        message.content = "[Message deleted]"
        message.file_path = None
        message.file_name = None
        message.file_size = None
        
        db.session.commit()
        
        # Emit message deletion
        from app import socketio
        socketio.emit('message_deleted', {
            'message_id': message_id,
            'conversation_id': message.conversation_id
        }, room=f'conversation_{message.conversation_id}')
        
        return jsonify({'success': True, 'message': 'Message deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Error deleting message: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error deleting message'}), 500

@messages_bp.route('/api/user_status/<int:user_id>', methods=['GET'])
@login_required
def get_user_status(user_id):
    """Get user's online status"""
    try:
        user = User.query.get_or_404(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user.id,
            'is_online': user.is_online(),
            'last_seen': user.last_seen.isoformat() if user.last_seen else None
        })
    except Exception as e:
        current_app.logger.error(f"Error getting user status: {e}")
        return jsonify({'success': False, 'message': 'Error getting user status'}), 500

@messages_bp.route('/api/suggested_users', methods=['GET'])
@login_required
def get_suggested_users():
    """Get suggested users for messaging"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Get friends first
        friendships = Friendship.query.filter(
            or_(
                Friendship.user_id == current_user.id,
                Friendship.friend_id == current_user.id
            ),
            Friendship.status == 'accepted'
        ).all()
        
        friend_ids = []
        for friendship in friendships:
            if friendship.user_id == current_user.id:
                friend_ids.append(friendship.friend_id)
            else:
                friend_ids.append(friendship.user_id)
        
        # Get existing conversations
        conversations = Conversation.query.filter(
            or_(
                Conversation.user1_id == current_user.id,
                Conversation.user2_id == current_user.id
            )
        ).all()
        
        conversation_user_ids = []
        for conv in conversations:
            if conv.user1_id == current_user.id:
                conversation_user_ids.append(conv.user2_id)
            else:
                conversation_user_ids.append(conv.user1_id)
        
        # Combine and remove duplicates
        exclude_ids = list(set(friend_ids + conversation_user_ids + [current_user.id]))
        
        # Get suggested users (not friends, not in conversations, most active)
        suggested_users = User.query.filter(
            User.id.notin_(exclude_ids),
            User.is_admin == False
        ).order_by(User.last_seen.desc()).limit(limit).all()
        
        users_data = []
        for user in suggested_users:
            users_data.append({
                'id': user.id,
                'name': user.name,
                'profile_picture': user.profile_picture or 'default_profile.png',
                'bio': user.bio or 'AB Engineering Student',
                'is_online': user.is_online(),
                'last_seen': user.last_seen.isoformat() if user.last_seen else None
            })
        
        return jsonify({'success': True, 'users': users_data})
    except Exception as e:
        current_app.logger.error(f"Error getting suggested users: {e}")
        return jsonify({'success': False, 'message': 'Error getting suggested users'}), 500
    
# app/messages/api.py - ADD MISSING ENDPOINTS

@messages_bp.route('/api/answer_call', methods=['POST'])
@login_required
def answer_call():
    """Answer an incoming call"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        call_session = CallSession.query.get(session_id)
        if not call_session or call_session.receiver_id != current_user.id:
            return jsonify({'success': False, 'message': 'Invalid call session'}), 400
        
        call_session.status = 'answered'
        call_session.started_at = datetime.utcnow()
        db.session.commit()
        
        # Notify caller
        socketio.emit('call_answered', {
            'session_id': session_id,
            'answerer_id': current_user.id
        }, room=f'user_{call_session.caller_id}')
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error answering call: {e}")
        return jsonify({'success': False, 'message': 'Error answering call'}), 500

@messages_bp.route('/api/end_call', methods=['POST'])
@login_required
def end_call():
    """End a call"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        duration = data.get('duration', 0)
        
        call_session = CallSession.query.get(session_id)
        if not call_session or current_user.id not in [call_session.caller_id, call_session.receiver_id]:
            return jsonify({'success': False, 'message': 'Invalid call session'}), 400
        
        call_session.status = 'ended'
        call_session.ended_at = datetime.utcnow()
        call_session.duration = duration
        db.session.commit()
        
        # Notify other party
        other_user_id = call_session.receiver_id if current_user.id == call_session.caller_id else call_session.caller_id
        socketio.emit('call_ended', {
            'session_id': session_id,
            'duration': duration
        }, room=f'user_{other_user_id}')
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error ending call: {e}")
        return jsonify({'success': False, 'message': 'Error ending call'}), 500

@messages_bp.route('/api/reject_call', methods=['POST'])
@login_required
def reject_call():
    """Reject an incoming call"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        call_session = CallSession.query.get(session_id)
        if not call_session or call_session.receiver_id != current_user.id:
            return jsonify({'success': False, 'message': 'Invalid call session'}), 400
        
        call_session.status = 'rejected'
        call_session.ended_at = datetime.utcnow()
        db.session.commit()
        
        # Notify caller
        socketio.emit('call_rejected', {
            'session_id': session_id
        }, room=f'user_{call_session.caller_id}')
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error rejecting call: {e}")
        return jsonify({'success': False, 'message': 'Error rejecting call'}), 500