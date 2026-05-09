# create_user.py
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Create admin user
    admin = User.query.filter_by(email='admin@test.com').first()
    if not admin:
        admin = User(name='Admin', email='admin@test.com')
        admin.set_password('admin123')
        admin.is_admin = True
        db.session.add(admin)
        print('✅ Admin user created: admin@test.com / admin123')
    else:
        print('⚠ Admin user already exists')
    
    # Create a test student
    student = User.query.filter_by(email='student@test.com').first()
    if not student:
        student = User(name='Student', email='student@test.com')
        student.set_password('student123')
        student.is_admin = False
        db.session.add(student)
        print('✅ Student user created: student@test.com / student123')
    else:
        print('⚠ Student user already exists')
    
    # Create another test user
    zoro = User.query.filter_by(email='zoro@test.com').first()
    if not zoro:
        zoro = User(name='Zoro', email='zoro@test.com')
        zoro.set_password('zoro123')
        db.session.add(zoro)
        print('✅ Zoro user created: zoro@test.com / zoro123')
    else:
        print('⚠ Zoro user already exists')
    
    db.session.commit()
    print("\n✅ All users created successfully!")
    
    # List all users
    users = User.query.all()
    print("\n📋 Current users:")
    for u in users:
        print(f"   - {u.name} ({u.email}) - {'Admin' if u.is_admin else 'Student'}")