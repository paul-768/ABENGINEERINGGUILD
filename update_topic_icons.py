# update_topic_icons.py
from app import create_app, db
from app.models import Topic

def update_topic_icons():
    app = create_app()
    with app.app_context():
        # Define icon mappings for topics
        icon_mappings = {
            'AREA I': 'fas fa-calculator',
            'AREA II': 'fas fa-flask', 
            'AREA III': 'fas fa-cogs',
            'Engineering Mathematics': 'fas fa-square-root-alt',
            'PAES Standards': 'fas fa-file-alt',
            'General Discussion': 'fas fa-comments'
        }
        
        topics = Topic.query.all()
        for topic in topics:
            if topic.name in icon_mappings:
                topic.icon = icon_mappings[topic.name]
            else:
                topic.icon = 'fas fa-folder'
            print(f"Updated {topic.name} with icon: {topic.icon}")
        
        db.session.commit()
        print("✓ All topic icons updated successfully!")

if __name__ == '__main__':
    update_topic_icons()