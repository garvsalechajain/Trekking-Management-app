from app import app, db, User, Trek
from werkzeug.security import generate_password_hash

def seed_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # 1. The Superuser
        admin_pw = generate_password_hash('admin')
        admin_user = User(username='admin', password_hash=admin_pw, role='Admin', status='Approved')
        db.session.add(admin_user)

        # 2. The Verified Crew
        staff_pw = generate_password_hash('staff')
        staff_user = User(username='Alex', password_hash=staff_pw, role='Staff', status='Approved')
        db.session.add(staff_user)
        
        staff_pw2 = generate_password_hash('staff3')
        staff_user2 = User(username='Sarah', password_hash=staff_pw2, role='Staff', status='Approved')
        db.session.add(staff_user2)
        
        pending_staff_pw = generate_password_hash('staff2')
        pending_staff_user = User(username='Bob', password_hash=pending_staff_pw, role='Staff', status='Pending')
        db.session.add(pending_staff_user)
        
        # Trekkers
        user_pw = generate_password_hash('user')
        trekker = User(username='john_doe', password_hash=user_pw, role='Trekker', status='Approved')
        db.session.add(trekker)
        
        trekker2 = User(username='jane_smith', password_hash=user_pw, role='Trekker', status='Approved')
        db.session.add(trekker2)
        
        trekker3 = User(username='michael_j', password_hash=user_pw, role='Trekker', status='Approved')
        db.session.add(trekker3)
        
        db.session.commit()
        
        # 3. The Sample Trails
        trek1 = Trek(name='Roopkund', location='Uttarakhand', difficulty='Hard', slots=15, status='Open', start_date='10/07/2026', end_date='20/07/2026', assigned_staff_id=staff_user.id)
        trek2 = Trek(name='Valley of Flowers', location='Uttarakhand', difficulty='Moderate', slots=20, status='Pending', start_date='25/07/2026', end_date='05/08/2026')
        trek3 = Trek(name='Kedarkantha', location='Uttarakhand', difficulty='Easy', slots=30, status='Open', start_date='01/08/2026', end_date='06/08/2026', assigned_staff_id=staff_user2.id)
        trek4 = Trek(name='Hampta Pass', location='Himachal Pradesh', difficulty='Moderate', slots=12, status='Open', start_date='15/08/2026', end_date='22/08/2026', assigned_staff_id=staff_user.id)
        trek5 = Trek(name='Everest Base Camp', location='Nepal', difficulty='Hard', slots=10, status='Closed', start_date='01/09/2026', end_date='15/09/2026', assigned_staff_id=staff_user2.id)
        
        db.session.add_all([trek1, trek2, trek3, trek4, trek5])
        db.session.commit()
        
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()