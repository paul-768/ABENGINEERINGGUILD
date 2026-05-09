# app/messages/routes.py - COMPLETE FIXED VERSION (No Inbox Template)
from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db, socketio, csrf
from app.models import Message, User, Notification, Conversation, GroupChat, GroupMember, GroupMessage
from datetime import datetime, timezone, timedelta
import os
import uuid
from werkzeug.utils import secure_filename

from app.messages import messages_bp

# Philippine Time = UTC+8
PHT = timezone(timedelta(hours=8))

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',
    'pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx',
    'mp3', 'wav', 'ogg', 'm4a',
    'mp4', 'webm'
}

def allowed_file(filename):
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}:
        return 'image'
    elif ext in {'mp3', 'wav', 'ogg', 'm4a'}:
        return 'voice'
    elif ext in {'mp4', 'webm'}:
        return 'video'
    else:
        return 'file'

def now_pht():
    """Return current time in Philippine Time (UTC+8)."""
    return datetime.now(PHT).replace(tzinfo=None)

def to_pht(dt):
    """Convert a naive UTC datetime to naive PHT datetime."""
    if dt is None:
        return None
    return (dt.replace(tzinfo=timezone.utc)).astimezone(PHT).replace(tzinfo=None)

def format_time_pht(dt):
    """Format datetime as 12-hour clock in PHT."""
    if dt is None:
        return ''
    pht_dt = to_pht(dt)
    return pht_dt.strftime('%I:%M %p')

def get_time_ago(dt):
    if not dt:
        return "Just now"
    now = now_pht()
    diff = now - to_pht(dt)
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

def get_user_conversations(user_id):
    conversations = Conversation.query.filter(
        (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
    ).order_by(Conversation.last_message_at.desc()).all()

    result = []
    for conv in conversations:
        other_user = conv.user2 if conv.user1_id == user_id else conv.user1
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(user_id)

        result.append({
            'id': conv.id,
            'type': 'direct',
            'other_user': {
                'id': other_user.id,
                'name': other_user.name,
                'profile_picture': other_user.profile_picture,
                'is_online': other_user.is_online()
            },
            'last_message': {
                'content': last_message.content if last_message else "No messages yet",
                'sender_id': last_message.sender_id if last_message else None
            },
            'unread_count': unread_count,
            'time_ago': get_time_ago(conv.last_message_at)
        })

    return result


@messages_bp.route('/')
@login_required
def index():
    """Main messages page - redirect to first conversation or show empty state"""
    conversations = get_user_conversations(current_user.id)
    
    if conversations:
        # Redirect to the first conversation
        return redirect(url_for('messages.conversation', conversation_id=conversations[0]['id']))
    else:
        # No conversations, show empty state
        return render_template('messages/no_conversations.html')


@messages_bp.route('/inbox')
@login_required
def inbox():
    """Redirect to main messages page"""
    return redirect(url_for('messages.index'))


@messages_bp.route('/conversation/<int:conversation_id>')
@login_required
def conversation(conversation_id):
    conv = Conversation.query.get_or_404(conversation_id)

    if current_user.id not in [conv.user1_id, conv.user2_id]:
        flash('Access denied', 'danger')
        return redirect(url_for('messages.index'))

    messages = Message.query.filter_by(
        conversation_id=conversation_id
    ).order_by(Message.created_at.asc()).all()

    unread_ids = []
    for msg in messages:
        if msg.receiver_id == current_user.id and not msg.is_read:
            msg.is_read = True
            msg.read_at = datetime.utcnow()
            unread_ids.append(msg.id)

    if unread_ids:
        db.session.commit()
        try:
            socketio.emit('message_read', {
                'conversation_id': conversation_id,
                'message_ids': unread_ids
            }, room=f'conversation_{conversation_id}')
        except Exception as e:
            print(f"Socket.IO error: {e}")

    other_user = conv.user2 if conv.user1_id == current_user.id else conv.user1
    
    # Get all conversations for the sidebar
    conversations = get_user_conversations(current_user.id)

    return render_template('messages/conversation.html',
                           conversation=conv,
                           other_user=other_user,
                           messages=messages,
                           conversations=conversations,
                           format_time_pht=format_time_pht)


@messages_bp.route('/start_conversation/<int:user_id>')
@login_required
def start_conversation(user_id):
    other_user = User.query.get_or_404(user_id)

    if other_user.id == current_user.id:
        flash('Cannot message yourself', 'warning')
        return redirect(url_for('messages.index'))

    existing = Conversation.query.filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == other_user.id)) |
        ((Conversation.user1_id == other_user.id) & (Conversation.user2_id == current_user.id))
    ).first()

    if existing:
        return redirect(url_for('messages.conversation', conversation_id=existing.id))

    conv = Conversation(
        user1_id=current_user.id,
        user2_id=other_user.id,
        last_message_at=datetime.utcnow()
    )
    db.session.add(conv)
    db.session.commit()

    return redirect(url_for('messages.conversation', conversation_id=conv.id))


@messages_bp.route('/send_message/<int:conversation_id>', methods=['POST'])
@login_required
@csrf.exempt
def send_message(conversation_id):
    try:
        conv = Conversation.query.get_or_404(conversation_id)

        if current_user.id not in [conv.user1_id, conv.user2_id]:
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        content = request.form.get('content', '').strip()

        if not content:
            return jsonify({'success': False, 'message': 'Message cannot be empty'}), 400

        receiver_id = conv.user2_id if current_user.id == conv.user1_id else conv.user1_id

        message = Message(
            content=content,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            conversation_id=conversation_id,
            message_type='text',
            created_at=datetime.utcnow()
        )

        conv.last_message_at = datetime.utcnow()

        db.session.add(message)
        db.session.commit()

        notification = Notification(
            user_id=receiver_id,
            title='New Message',
            message=f'{current_user.name}: {content[:50]}',
            notification_type='message',
            related_id=message.id,
            action_url=url_for('messages.conversation', conversation_id=conversation_id)
        )
        db.session.add(notification)
        db.session.commit()

        message_data = {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender_id,
            'sender_name': message.sender.name,
            'sender_avatar': message.sender.profile_picture or 'default.png',
            'conversation_id': message.conversation_id,
            'message_type': message.message_type,
            'created_at': message.created_at.isoformat(),
            'formatted_time': format_time_pht(message.created_at),
            'is_read': message.is_read
        }

        try:
            socketio.emit('new_message', {
                'conversation_id': conversation_id,
                'message_data': message_data
            }, room=f'conversation_{conversation_id}')
        except Exception as e:
            print(f"Socket.IO error: {e}")

        return jsonify({
            'success': True,
            'message': 'Message sent',
            'message_data': message_data
        })

    except Exception as e:
        print(f"Error sending message: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@messages_bp.route('/upload_file/<int:conversation_id>', methods=['POST'])
@login_required
@csrf.exempt
def upload_file(conversation_id):
    try:
        conv = Conversation.query.get_or_404(conversation_id)

        if current_user.id not in [conv.user1_id, conv.user2_id]:
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'File type not allowed'}), 400

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"

        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'messages')
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)

        file_size = os.path.getsize(filepath)
        file_type = get_file_type(filename)

        receiver_id = conv.user2_id if current_user.id == conv.user1_id else conv.user1_id

        message = Message(
            content=filename,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            conversation_id=conversation_id,
            message_type=file_type,
            file_path=unique_filename,
            file_name=filename,
            file_size=file_size,
            created_at=datetime.utcnow()
        )

        conv.last_message_at = datetime.utcnow()

        db.session.add(message)
        db.session.commit()

        notification = Notification(
            user_id=receiver_id,
            title='New Message',
            message=f'{current_user.name} sent a {file_type}',
            notification_type='message',
            related_id=message.id,
            action_url=url_for('messages.conversation', conversation_id=conversation_id)
        )
        db.session.add(notification)
        db.session.commit()

        message_data = {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender_id,
            'sender_name': message.sender.name,
            'conversation_id': message.conversation_id,
            'message_type': message.message_type,
            'file_path': message.file_path,
            'file_name': message.file_name,
            'file_size': message.file_size,
            'created_at': message.created_at.isoformat(),
            'formatted_time': format_time_pht(message.created_at),
            'is_read': message.is_read
        }

        try:
            socketio.emit('new_message', {
                'conversation_id': conversation_id,
                'message_data': message_data
            }, room=f'conversation_{conversation_id}')
        except Exception as e:
            print(f"Socket.IO error: {e}")

        return jsonify({
            'success': True,
            'message': 'File uploaded',
            'message_data': message_data
        })

    except Exception as e:
        print(f"Error uploading file: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@messages_bp.route('/search_users')
@login_required
def search_users():
    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify({'users': []})

    users = User.query.filter(
        (User.name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%')),
        User.id != current_user.id
    ).limit(20).all()

    result = [{
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'profile_picture': u.profile_picture
    } for u in users]

    return jsonify({'users': result})


@messages_bp.route('/mark_read/<int:conversation_id>', methods=['POST'])
@login_required
@csrf.exempt
def mark_read(conversation_id):
    try:
        conv = Conversation.query.get_or_404(conversation_id)

        if current_user.id not in [conv.user1_id, conv.user2_id]:
            return jsonify({'success': False}), 403

        messages = Message.query.filter_by(
            conversation_id=conversation_id,
            receiver_id=current_user.id,
            is_read=False
        ).all()

        message_ids = []
        for msg in messages:
            msg.is_read = True
            msg.read_at = datetime.utcnow()
            message_ids.append(msg.id)

        db.session.commit()

        if message_ids:
            try:
                socketio.emit('message_read', {
                    'conversation_id': conversation_id,
                    'message_ids': message_ids
                }, room=f'conversation_{conversation_id}')
            except Exception as e:
                print(f"Socket.IO error: {e}")

        return jsonify({'success': True, 'count': len(message_ids)})

    except Exception as e:
        print(f"Error marking read: {e}")
        return jsonify({'success': False}), 500


@messages_bp.route('/unsend_message/<int:message_id>', methods=['POST'])
@login_required
def unsend_message(message_id):
    """Delete a single message (unsend)"""
    try:
        message = Message.query.get_or_404(message_id)
        
        if message.sender_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        conversation_id = message.conversation_id
        
        db.session.delete(message)
        db.session.commit()
        
        conv = Conversation.query.get(conversation_id)
        if conv:
            last_msg = conv.get_last_message()
            if last_msg:
                conv.last_message_at = last_msg.created_at
            else:
                conv.last_message_at = datetime.utcnow()
            db.session.commit()
        
        try:
            socketio.emit('message_unsent', {
                'conversation_id': conversation_id,
                'message_id': message_id
            }, room=f'conversation_{conversation_id}')
        except Exception as e:
            print(f"Socket.IO error: {e}")
        
        return jsonify({'success': True, 'message': 'Message unsent successfully'})
        
    except Exception as e:
        print(f"Error unsending message: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@messages_bp.route('/edit_message/<int:message_id>', methods=['POST'])
@login_required
def edit_message(message_id):
    """Edit an existing message"""
    try:
        message = Message.query.get_or_404(message_id)
        
        if message.sender_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        if not data:
            data = request.form
        
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return jsonify({'success': False, 'message': 'Content cannot be empty'}), 400
        
        message.content = new_content
        message.is_edited = True
        db.session.commit()
        
        try:
            socketio.emit('message_edited', {
                'conversation_id': message.conversation_id,
                'message_id': message_id,
                'new_content': new_content
            }, room=f'conversation_{message.conversation_id}')
        except Exception as e:
            print(f"Socket.IO error: {e}")
        
        return jsonify({'success': True, 'message': 'Message edited successfully'})
        
    except Exception as e:
        print(f"Error editing message: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@messages_bp.route('/delete_messages', methods=['POST'])
@login_required
def delete_messages():
    """Delete multiple messages"""
    try:
        data = request.get_json()
        message_ids = data.get('message_ids', [])
        conversation_id = data.get('conversation_id')
        
        if not message_ids:
            return jsonify({'success': False, 'message': 'No messages selected'}), 400
        
        messages = Message.query.filter(
            Message.id.in_(message_ids),
            Message.sender_id == current_user.id
        ).all()
        
        deleted_ids = []
        for message in messages:
            deleted_ids.append(message.id)
            db.session.delete(message)
        
        db.session.commit()
        
        if conversation_id:
            conv = Conversation.query.get(conversation_id)
            if conv:
                last_msg = conv.get_last_message()
                if last_msg:
                    conv.last_message_at = last_msg.created_at
                else:
                    conv.last_message_at = datetime.utcnow()
                db.session.commit()
        
        if deleted_ids:
            try:
                socketio.emit('messages_deleted', {
                    'conversation_id': conversation_id,
                    'message_ids': deleted_ids
                }, room=f'conversation_{conversation_id}')
            except Exception as e:
                print(f"Socket.IO error: {e}")
        
        return jsonify({'success': True, 'deleted_count': len(deleted_ids), 'message': f'{len(deleted_ids)} messages deleted'})
        
    except Exception as e:
        print(f"Error deleting messages: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@messages_bp.route('/api/conversation/<int:conversation_id>/messages', methods=['GET'])
@login_required
def get_conversation_messages(conversation_id):
    """API endpoint to get messages for a conversation"""
    try:
        conv = Conversation.query.get_or_404(conversation_id)
        
        if current_user.id not in [conv.user1_id, conv.user2_id]:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at.asc()).all()
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'content': msg.content,
                'sender_id': msg.sender_id,
                'sender_name': msg.sender.name,
                'conversation_id': msg.conversation_id,
                'message_type': msg.message_type,
                'file_path': msg.file_path,
                'file_name': msg.file_name,
                'file_size': msg.file_size,
                'created_at': msg.created_at.isoformat(),
                'formatted_time': format_time_pht(msg.created_at),
                'is_read': msg.is_read,
                'is_edited': getattr(msg, 'is_edited', False)
            })
        
        return jsonify({'success': True, 'messages': messages_data})
        
    except Exception as e:
        print(f"Error getting messages: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@messages_bp.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '')
        is_private = request.form.get('is_private') == 'true'
        member_ids = request.form.getlist('members[]')

        if not name:
            flash('Group name is required', 'danger')
            return redirect(url_for('messages.create_group'))

        group = GroupChat(
            name=name,
            description=description,
            owner_id=current_user.id,
            created_by=current_user.id,
            is_private=is_private,
            member_count=1
        )
        db.session.add(group)
        db.session.flush()

        member = GroupMember(
            group_id=group.id,
            user_id=current_user.id,
            role='owner'
        )
        db.session.add(member)

        for member_id in member_ids:
            try:
                uid = int(member_id)
                if uid != current_user.id:
                    new_member = GroupMember(
                        group_id=group.id,
                        user_id=uid,
                        role='member'
                    )
                    db.session.add(new_member)
                    group.member_count += 1
            except (ValueError, TypeError):
                continue

        db.session.commit()

        flash(f'Group "{name}" created successfully!', 'success')
        return redirect(url_for('messages.index'))

    return render_template('messages/create_group.html')


@messages_bp.route('/group/<int:group_id>')
@login_required
def group_conversation(group_id):
    group = GroupChat.query.get_or_404(group_id)

    member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not member and not group.is_private:
        member = GroupMember(group_id=group_id, user_id=current_user.id, role='member')
        db.session.add(member)
        group.member_count += 1
        db.session.commit()
    elif not member:
        flash('You are not a member of this group', 'danger')
        return redirect(url_for('messages.index'))

    messages = group.messages.order_by(GroupMessage.created_at.asc()).all()
    members = group.members.all()

    return render_template('messages/group_conversation.html',
                           group=group,
                           messages=messages,
                           members=members)

@messages_bp.route('/api/message/<int:message_id>/edit', methods=['POST'])
@login_required
def edit_message_api(message_id):
    """Edit a sent message (only within 5 minutes)"""
    message = Message.query.get_or_404(message_id)
    
    if message.sender_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Check if message is within 5 minutes of sending
    time_diff = datetime.utcnow() - message.created_at
    if time_diff.total_seconds() > 300:  # 5 minutes
        return jsonify({'success': False, 'message': 'Messages can only be edited within 5 minutes of sending'}), 400
    
    data = request.get_json()
    new_content = data.get('content', '').strip()
    
    if not new_content:
        return jsonify({'success': False, 'message': 'Content cannot be empty'}), 400
    
    message.content = new_content
    message.is_edited = True
    db.session.commit()
    
    # Emit socket event for real-time update
    from flask_socketio import emit
    emit('message_edited', {
        'message_id': message.id,
        'conversation_id': message.conversation_id,
        'new_content': new_content,
        'is_edited': True
    }, room=f"conversation_{message.conversation_id}", namespace='/')
    
    return jsonify({
    'success': True, 
    'message': 'Message updated',
    'message_data': {
        'id': message.id,
        'content': message.content,
        'is_edited': message.is_edited
    }
})


@messages_bp.route('/api/message/<int:message_id>/delete', methods=['DELETE'])
@login_required
def delete_message_api(message_id):
    """Delete a message"""
    message = Message.query.get_or_404(message_id)
    
    if message.sender_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get conversation_id before deleting
    conversation_id = message.conversation_id
    
    # Emit socket event before deleting
    from flask_socketio import emit
    emit('message_deleted', {
        'message_id': message.id,
        'conversation_id': conversation_id
    }, room=f"conversation_{conversation_id}", namespace='/')
    
    db.session.delete(message)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Message deleted'})