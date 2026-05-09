# app/messages/events.py - COMPLETE REAL-TIME MESSAGING (FIXED VERSION)
from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import Message, Conversation, User, Notification, MessageReaction, CallSession, GroupChat, GroupMember, GroupMessage
from datetime import datetime
import json
import uuid

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        print(f"✅ User {current_user.id} ({current_user.name}) connected to messaging")
        # Join user's personal room for direct notifications
        join_room(f'user_{current_user.id}')
        # Update last seen
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Notify friends about online status
        notify_friends_online_status(current_user.id, True)
        emit('connected', {'status': 'connected', 'user_id': current_user.id})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        print(f"❌ User {current_user.id} ({current_user.name}) disconnected")
        # Update last seen
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Notify friends about offline status
        notify_friends_online_status(current_user.id, False)

def notify_friends_online_status(user_id, is_online):
    """Notify friends about online status change"""
    try:
        user = User.query.get(user_id)
        if not user:
            return
        
        friends = user.get_friends()
        for friend in friends:
            emit('friend_online_status', {
                'user_id': user_id,
                'user_name': user.name,
                'is_online': is_online,
                'last_seen': user.last_seen.isoformat() if not is_online else None
            }, room=f'user_{friend.id}')
    except Exception as e:
        print(f"Error notifying friends: {e}")

@socketio.on('join_conversation')
def handle_join_conversation(data):
    """Join a conversation room for real-time updates"""
    if current_user.is_authenticated:
        conversation_id = data.get('conversation_id')
        if conversation_id:
            # Verify user is part of this conversation
            conversation = Conversation.query.get(conversation_id)
            if conversation and current_user.id in [conversation.user1_id, conversation.user2_id]:
                room = f'conversation_{conversation_id}'
                join_room(room)
                print(f"User {current_user.id} joined conversation {conversation_id}")
                emit('joined_conversation', {'conversation_id': conversation_id})

@socketio.on('leave_conversation')
def handle_leave_conversation(data):
    """Leave a conversation room"""
    if current_user.is_authenticated:
        conversation_id = data.get('conversation_id')
        if conversation_id:
            room = f'conversation_{conversation_id}'
            leave_room(room)
            print(f"User {current_user.id} left conversation {conversation_id}")

@socketio.on('send_message')
def handle_send_message(data):
    """Handle real-time message sending"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Not authenticated'})
        return
    
    conversation_id = data.get('conversation_id')
    content = data.get('content', '').strip()
    message_type = data.get('message_type', 'text')
    file_data = data.get('file_data')
    reply_to_id = data.get('reply_to_id')
    
    if not conversation_id:
        emit('error', {'message': 'No conversation ID provided'})
        return
    
    conversation = Conversation.query.get(conversation_id)
    if not conversation or current_user.id not in [conversation.user1_id, conversation.user2_id]:
        emit('error', {'message': 'Access denied'})
        return
    
    # Create message
    receiver_id = conversation.user2_id if current_user.id == conversation.user1_id else conversation.user1_id
    
    message = Message(
        content=content if message_type == 'text' else None,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        conversation_id=conversation_id,
        message_type=message_type,
        reply_to_id=int(reply_to_id) if reply_to_id else None,
        delivered_at=datetime.utcnow()
    )
    
    # Handle file attachments
    if message_type in ['image', 'video', 'audio', 'file'] and file_data:
        message.file_path = file_data.get('file_path')
        message.file_name = file_data.get('file_name')
        message.file_size = file_data.get('file_size')
        message.thumbnail_path = file_data.get('thumbnail_path')
        message.duration = file_data.get('duration')
    
    # Update conversation timestamp
    conversation.last_message_at = datetime.utcnow()
    
    db.session.add(message)
    db.session.commit()
    
    # Prepare message data for emission
    message_data = prepare_message_data(message)
    
    # Emit to conversation room
    emit('new_message', {
        'conversation_id': conversation_id,
        'message_data': message_data
    }, room=f'conversation_{conversation_id}')
    
    # Send notification to receiver
    try:
        notification = Notification(
            user_id=receiver_id,
            title='New Message',
            message=f'{current_user.name}: {content[:50] if content else f"Sent a {message_type}"}',
            notification_type='message',
            related_id=message.id,
            action_url=f'/messages/conversation/{conversation_id}'
        )
        db.session.add(notification)
        db.session.commit()
        
        emit('message_notification', {
            'conversation_id': conversation_id,
            'message_preview': content[:50] if content else f"Sent a {message_type}",
            'sender_name': current_user.name,
            'sender_id': current_user.id,
            'unread_count': conversation.get_unread_count(receiver_id),
            'message_data': message_data
        }, room=f'user_{receiver_id}')
    except Exception as e:
        print(f"Error sending notification: {e}")
    
    # Send success response back to sender
    emit('message_sent', {
        'success': True,
        'message_data': message_data
    }, room=f'user_{current_user.id}')

@socketio.on('send_group_message')
def handle_send_group_message(data):
    """Handle group message sending"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Not authenticated'})
        return
    
    group_id = data.get('group_id')
    content = data.get('content', '').strip()
    message_type = data.get('message_type', 'text')
    file_data = data.get('file_data')
    
    if not group_id:
        emit('error', {'message': 'No group ID provided'})
        return
    
    # Verify user is a member
    member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not member:
        emit('error', {'message': 'Not a member of this group'})
        return
    
    group = GroupChat.query.get(group_id)
    if not group:
        emit('error', {'message': 'Group not found'})
        return
    
    # Create group message
    message = GroupMessage(
        content=content if message_type == 'text' else None,
        sender_id=current_user.id,
        group_id=group_id,
        message_type=message_type,
        read_by='[]'
    )
    
    # Handle file attachments
    if message_type in ['image', 'video', 'audio', 'file'] and file_data:
        message.file_path = file_data.get('file_path')
        message.file_name = file_data.get('file_name')
        message.file_size = file_data.get('file_size')
        message.thumbnail_path = file_data.get('thumbnail_path')
        message.duration = file_data.get('duration')
    
    # Update group timestamp
    group.last_message_at = datetime.utcnow()
    
    db.session.add(message)
    db.session.commit()
    
    # Prepare message data
    message_data = prepare_group_message_data(message)
    
    # Emit to group room
    emit('new_group_message', {
        'group_id': group_id,
        'message_data': message_data
    }, room=f'group_{group_id}')
    
    # Notify all members except sender
    members = GroupMember.query.filter_by(group_id=group_id).all()
    for m in members:
        if m.user_id != current_user.id:
            try:
                notification = Notification(
                    user_id=m.user_id,
                    title=f'New message in {group.name}',
                    message=f'{current_user.name}: {content[:50] if content else f"Sent a {message_type}"}',
                    notification_type='group_message',
                    related_id=message.id,
                    action_url=f'/messages/group/{group_id}'
                )
                db.session.add(notification)
            except Exception as e:
                print(f"Error creating notification: {e}")
    
    db.session.commit()
    
    emit('message_sent', {
        'success': True,
        'message_data': message_data
    }, room=f'user_{current_user.id}')

@socketio.on('react_to_message')
def handle_message_reaction(data):
    """Handle message reactions"""
    if not current_user.is_authenticated:
        return
    
    message_id = data.get('message_id')
    reaction = data.get('reaction')
    is_group = data.get('is_group', False)
    
    if not message_id or not reaction:
        return
    
    if is_group:
        message = GroupMessage.query.get(message_id)
        if not message:
            return
    else:
        message = Message.query.get(message_id)
        if not message:
            return
    
    # For direct messages, verify user has access
    if not is_group:
        if current_user.id not in [message.sender_id, message.receiver_id]:
            return
    
    # Check if user already reacted
    existing_reaction = MessageReaction.query.filter_by(
        message_id=message_id,
        user_id=current_user.id
    ).first()
    
    if existing_reaction:
        if existing_reaction.reaction == reaction:
            # Remove reaction if same emoji clicked
            db.session.delete(existing_reaction)
            reacted = False
        else:
            # Update reaction
            existing_reaction.reaction = reaction
            reacted = True
    else:
        # Create new reaction
        new_reaction = MessageReaction(
            message_id=message_id,
            user_id=current_user.id,
            reaction=reaction
        )
        db.session.add(new_reaction)
        reacted = True
    
    db.session.commit()
    
    # Get reaction count
    reaction_count = MessageReaction.query.filter_by(message_id=message_id).count()
    
    # Determine which room to emit to
    if is_group:
        room = f'group_{message.group_id}'
    else:
        room = f'conversation_{message.conversation_id}'
    
    # Emit reaction update
    emit('message_reaction', {
        'message_id': message_id,
        'user_id': current_user.id,
        'user_name': current_user.name,
        'reaction': reaction,
        'reacted': reacted,
        'reaction_count': reaction_count,
        'is_group': is_group
    }, room=room)

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    if current_user.is_authenticated:
        conversation_id = data.get('conversation_id')
        
        if conversation_id:
            conversation = Conversation.query.get(conversation_id)
            if conversation and current_user.id in [conversation.user1_id, conversation.user2_id]:
                other_user_id = conversation.user2_id if current_user.id == conversation.user1_id else conversation.user1_id
                emit('user_typing', {
                    'conversation_id': conversation_id,
                    'user_id': current_user.id,
                    'user_name': current_user.name,
                    'typing': True
                }, room=f'user_{other_user_id}')

@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Handle stop typing indicator"""
    if current_user.is_authenticated:
        conversation_id = data.get('conversation_id')
        
        if conversation_id:
            conversation = Conversation.query.get(conversation_id)
            if conversation and current_user.id in [conversation.user1_id, conversation.user2_id]:
                other_user_id = conversation.user2_id if current_user.id == conversation.user1_id else conversation.user1_id
                emit('user_typing', {
                    'conversation_id': conversation_id,
                    'user_id': current_user.id,
                    'user_name': current_user.name,
                    'typing': False
                }, room=f'user_{other_user_id}')

@socketio.on('group_typing')
def handle_group_typing(data):
    """Handle typing indicator for groups"""
    if current_user.is_authenticated:
        group_id = data.get('group_id')
        is_typing = data.get('typing', True)
        
        if group_id:
            emit('group_user_typing', {
                'group_id': group_id,
                'user_id': current_user.id,
                'user_name': current_user.name,
                'typing': is_typing
            }, room=f'group_{group_id}')

@socketio.on('mark_messages_read')
def handle_mark_messages_read(data):
    """Mark messages as read"""
    if current_user.is_authenticated:
        conversation_id = data.get('conversation_id')
        is_group = data.get('is_group', False)
        
        if is_group:
            group_id = conversation_id
            # Mark group messages as read
            unread_messages = GroupMessage.query.filter(
                GroupMessage.group_id == group_id,
                ~GroupMessage.read_by.contains(str(current_user.id))
            ).all()
            
            for msg in unread_messages:
                read_by = json.loads(msg.read_by) if msg.read_by else []
                if current_user.id not in read_by:
                    read_by.append(current_user.id)
                    msg.read_by = json.dumps(read_by)
            
            db.session.commit()
            
            emit('group_messages_read', {
                'group_id': group_id,
                'read_by': current_user.id,
                'read_at': datetime.utcnow().isoformat()
            }, room=f'group_{group_id}')
            
        else:
            conversation = Conversation.query.get(conversation_id)
            if conversation and current_user.id in [conversation.user1_id, conversation.user2_id]:
                # Mark all unread messages as read
                unread_messages = Message.query.filter(
                    Message.conversation_id == conversation_id,
                    Message.receiver_id == current_user.id,
                    Message.is_read == False
                ).all()
                
                for msg in unread_messages:
                    msg.is_read = True
                    msg.read_at = datetime.utcnow()
                
                db.session.commit()
                
                other_user_id = conversation.user2_id if current_user.id == conversation.user1_id else conversation.user1_id
                emit('messages_read', {
                    'conversation_id': conversation_id,
                    'read_by': current_user.id,
                    'read_at': datetime.utcnow().isoformat()
                }, room=f'user_{other_user_id}')

@socketio.on('initiate_call')
def handle_initiate_call(data):
    """Initiate a voice or video call"""
    if not current_user.is_authenticated:
        return
    
    receiver_id = data.get('receiver_id')
    call_type = data.get('call_type', 'voice')
    call_id = str(uuid.uuid4())
    
    if not receiver_id:
        return
    
    receiver = User.query.get(receiver_id)
    if not receiver:
        return
    
    # Create call session
    call_session = CallSession(
        caller_id=current_user.id,
        receiver_id=receiver_id,
        call_type=call_type,
        status='ringing'
    )
    db.session.add(call_session)
    db.session.commit()
    
    # Notify receiver
    emit('incoming_call', {
        'call_id': call_id,
        'caller_id': current_user.id,
        'caller_name': current_user.name,
        'call_type': call_type,
        'session_id': call_session.id
    }, room=f'user_{receiver_id}')
    
    # Send call initiated confirmation to caller
    emit('call_initiated', {
        'call_id': call_id,
        'session_id': call_session.id
    }, room=f'user_{current_user.id}')

@socketio.on('answer_call')
def handle_answer_call(data):
    """Answer an incoming call"""
    call_session_id = data.get('session_id')
    
    call_session = CallSession.query.get(call_session_id)
    if not call_session or call_session.receiver_id != current_user.id:
        return
    
    call_session.status = 'answered'
    call_session.started_at = datetime.utcnow()
    db.session.commit()
    
    # Notify caller
    emit('call_answered', {
        'session_id': call_session_id,
        'answerer_id': current_user.id,
        'answerer_name': current_user.name
    }, room=f'user_{call_session.caller_id}')

@socketio.on('end_call')
def handle_end_call(data):
    """End an ongoing call"""
    call_session_id = data.get('session_id')
    duration = data.get('duration', 0)
    
    call_session = CallSession.query.get(call_session_id)
    if not call_session or current_user.id not in [call_session.caller_id, call_session.receiver_id]:
        return
    
    call_session.status = 'ended'
    call_session.ended_at = datetime.utcnow()
    call_session.duration = duration
    db.session.commit()
    
    # Notify both parties
    other_user_id = call_session.receiver_id if current_user.id == call_session.caller_id else call_session.caller_id
    emit('call_ended', {
        'session_id': call_session_id,
        'duration': duration,
        'ended_by': current_user.id
    }, room=f'user_{other_user_id}')
    
    emit('call_ended', {
        'session_id': call_session_id,
        'duration': duration,
        'ended_by': current_user.id
    }, room=f'user_{current_user.id}')

@socketio.on('reject_call')
def handle_reject_call(data):
    """Reject an incoming call"""
    call_session_id = data.get('session_id')
    
    call_session = CallSession.query.get(call_session_id)
    if not call_session or call_session.receiver_id != current_user.id:
        return
    
    call_session.status = 'rejected'
    call_session.ended_at = datetime.utcnow()
    db.session.commit()
    
    # Notify caller
    emit('call_rejected', {
        'session_id': call_session_id,
        'rejected_by': current_user.id
    }, room=f'user_{call_session.caller_id}')

def prepare_message_data(message):
    """Prepare message data for socket emission"""
    replied_message = None
    if message.reply_to_id:
        original_msg = Message.query.get(message.reply_to_id)
        if original_msg:
            replied_message = {
                'id': original_msg.id,
                'content': original_msg.content,
                'sender_name': original_msg.sender.name,
                'message_type': original_msg.message_type
            }
    
    return {
        'id': message.id,
        'content': message.content,
        'sender_id': message.sender_id,
        'sender_name': message.sender.name,
        'sender_avatar': message.sender.profile_picture or 'default_profile.png',
        'conversation_id': message.conversation_id,
        'message_type': message.message_type,
        'file_path': message.file_path,
        'file_name': message.file_name,
        'file_size': message.file_size,
        'thumbnail_path': message.thumbnail_path,
        'duration': message.duration,
        'is_read': message.is_read,
        'created_at': message.created_at.isoformat(),
        'formatted_time': message.created_at.strftime('%I:%M %p'),
        'time_ago': get_time_ago(message.created_at),
        'reactions': [{
            'user_id': reaction.user_id,
            'user_name': reaction.user.name,
            'reaction': reaction.reaction
        } for reaction in message.reactions],
        'reply_to': replied_message
    }

def prepare_group_message_data(message):
    """Prepare group message data for socket emission"""
    return {
        'id': message.id,
        'content': message.content,
        'sender_id': message.sender_id,
        'sender_name': message.sender.name,
        'sender_avatar': message.sender.profile_picture or 'default_profile.png',
        'group_id': message.group_id,
        'message_type': message.message_type,
        'file_path': message.file_path,
        'file_name': message.file_name,
        'file_size': message.file_size,
        'thumbnail_path': message.thumbnail_path,
        'duration': message.duration,
        'created_at': message.created_at.isoformat(),
        'formatted_time': message.created_at.strftime('%I:%M %p'),
        'time_ago': get_time_ago(message.created_at),
        'read_by': json.loads(message.read_by) if message.read_by else []
    }

def get_time_ago(dt):
    """Get human-readable time ago string"""
    if not dt:
        return "Just now"
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days // 365}y ago"
    elif diff.days > 30:
        return f"{diff.days // 30}mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "Just now"