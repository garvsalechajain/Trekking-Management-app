from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SECRET_KEY'] = 'trekking_secret_key_123'
db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'Admin', 'Staff', 'Trekker'
    status = db.Column(db.String(50), default='Approved') # 'Pending', 'Approved', 'Blacklisted'
    contact_details = db.Column(db.String(255), nullable=True)

class Trek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    slots = db.Column(db.Integer, default=10, nullable=False)
    status = db.Column(db.String(50), default='Open') # 'Pending', 'Open', 'Closed', 'Completed'
    start_date = db.Column(db.String(100), nullable=False)
    end_date = db.Column(db.String(100), nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    assigned_staff = db.relationship('User', foreign_keys=[assigned_staff_id], backref='assigned_treks')

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trekker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    num_spots = db.Column(db.Integer, default=1, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Booked') # 'Booked', 'Completed'
    
    trekker = db.relationship('User', foreign_keys=[trekker_id], backref='bookings')
    trek = db.relationship('Trek', foreign_keys=[trek_id], backref='bookings')


# --- AUTH ROUTES ---
@app.route('/')
def home():
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'Admin': return redirect(url_for('admin_dashboard'))
        elif role == 'Staff': return redirect(url_for('staff_dashboard'))
        elif role == 'Trekker': return redirect(url_for('user_dashboard'))
    return render_template('home.html')

@app.route('/login-submit', methods=['POST'])
def login_submit():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        if user.role != role:
            flash("Invalid role selected for this account.", "danger")
            return redirect(url_for('home'))
        if user.status == 'Blacklisted':
            flash("Your account is blacklisted.", "danger")
            return redirect(url_for('home'))
        if user.role == 'Staff' and user.status == 'Pending':
            flash("Your staff account is pending admin approval.", "warning")
            return redirect(url_for('home'))
        
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['username'] = user.username
        
        flash("Logged in successfully.", "success")
        if user.role == 'Admin': return redirect(url_for('admin_dashboard'))
        elif user.role == 'Staff': return redirect(url_for('staff_dashboard'))
        elif user.role == 'Trekker': return redirect(url_for('user_dashboard'))
    
    flash("Invalid credentials.", "danger")
    return redirect(url_for('home'))

@app.route('/register')
def register():
    return render_template('register.html')
 
@app.route('/register-submit', methods=['POST'])
def register_submit():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("Username already exists.", "danger")
        return redirect(url_for('register'))

    hashed_pw = generate_password_hash(password)
    status = 'Pending' if role == 'Staff' else 'Approved'
    
    new_user = User(username=username, password_hash=hashed_pw, role=role, status=status)
    db.session.add(new_user)
    db.session.commit()

    flash("Registration successful. Please login.", "success")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('home'))

# --- ADMIN ROUTES ---
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='Trekker').count() 
    total_staff = User.query.filter_by(role='Staff').count() 
    total_bookings = Booking.query.count()
    
    pending_staff = User.query.filter_by(role='Staff', status='Pending').all()
    treks = Trek.query.all()
    users = User.query.filter_by(role='Trekker').all()
    staffs = User.query.filter_by(role='Staff').all()
    
    return render_template('admin/dashboard.html', 
                           total_treks=total_treks, total_users=total_users, 
                           total_staff=total_staff, total_bookings=total_bookings,
                           pending_staff=pending_staff, treks=treks, users=users, staffs=staffs)

@app.route('/admin/new_trek', methods=['GET', 'POST'])
def new_trek():
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        difficulty = request.form.get('difficulty')
        slots = request.form.get('slots')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        new_t = Trek(name=name, location=location, difficulty=difficulty, slots=slots,
                     start_date=start_date, end_date=end_date, status='Open')
        db.session.add(new_t)
        db.session.commit()
        flash("Trek created successfully.", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/new_trek.html')

@app.route('/admin/edit_trek/<int:trek_id>', methods=['GET', 'POST'])
def edit_trek(trek_id):
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    trek = Trek.query.get_or_404(trek_id)
    if request.method == 'POST':
        trek.name = request.form.get('name')
        trek.location = request.form.get('location')
        trek.difficulty = request.form.get('difficulty')
        trek.slots = int(request.form.get('slots', trek.slots))
        trek.start_date = request.form.get('start_date')
        trek.end_date = request.form.get('end_date')
        trek.status = request.form.get('status')
        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/edit_trek.html', trek=trek)

@app.route('/admin/delete_trek/<int:trek_id>', methods=['POST'])
def delete_trek(trek_id):
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    trek = Trek.query.get_or_404(trek_id)
    Booking.query.filter_by(trek_id=trek.id).delete()
    db.session.delete(trek)
    db.session.commit()
    flash("Trek deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_staff/<int:staff_id>', methods=['POST'])
def approve_staff(staff_id):
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    staff = User.query.get_or_404(staff_id)
    if staff.role == 'Staff':
        staff.status = 'Approved'
        db.session.commit()
        flash(f"Staff {staff.username} approved.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/assign_staff', methods=['POST'])
def assign_staff():
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    trek_id = request.form.get('trek_id')
    staff_id = request.form.get('staff_id')
    trek = Trek.query.get(trek_id)
    if trek:
        trek.assigned_staff_id = staff_id
        db.session.commit()
        flash("Staff assigned to trek successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/blacklist/<int:user_id>', methods=['POST'])
def blacklist_user(user_id):
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    user = User.query.get_or_404(user_id)
    user.status = 'Blacklisted'
    db.session.commit()
    flash(f"User {user.username} has been blacklisted.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unblacklist/<int:user_id>', methods=['POST'])
def unblacklist_user(user_id):
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    user = User.query.get_or_404(user_id)
    user.status = 'Approved'
    db.session.commit()
    flash(f"User {user.username} has been unblacklisted.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/search')
def admin_search():
    if 'user_id' not in session or session.get('user_role') != 'Admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    query = request.args.get('q', '').lower()
    treks = Trek.query.filter(
        Trek.name.ilike(f'%{query}%') | Trek.location.ilike(f'%{query}%') | Trek.id.like(f'%{query}%')
    ).all()
    
    matched_users = User.query.filter(
        User.role == 'Trekker',
        (User.username.ilike(f'%{query}%') | User.id.like(f'%{query}%'))
    ).all()
    
    matched_staffs = User.query.filter(
        User.role == 'Staff',
        (User.username.ilike(f'%{query}%') | User.id.like(f'%{query}%'))
    ).all()
    
    all_staffs = User.query.filter_by(role='Staff').all()
    
    return render_template('admin/search_results.html', query=query, treks=treks, users=matched_users, matched_staffs=matched_staffs, staffs=all_staffs)

# --- STAFF ROUTES ---
@app.route('/staff/dashboard')
def staff_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'Staff':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    assigned_treks = Trek.query.filter_by(assigned_staff_id=user_id).all()
    return render_template('staff/dashboard.html', treks=assigned_treks)

@app.route('/staff/manage_trek/<int:trek_id>', methods=['GET', 'POST'])
def manage_trek(trek_id):
    if 'user_id' not in session or session.get('user_role') != 'Staff':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    trek = Trek.query.filter_by(id=trek_id, assigned_staff_id=user_id).first_or_404()
    
    if request.method == 'POST':
        trek.slots = request.form.get('slots')
        trek.status = request.form.get('status')
        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for('staff_dashboard'))
        
    bookings = Booking.query.filter_by(trek_id=trek_id).all()
    return render_template('staff/manage_trek.html', trek=trek, bookings=bookings)

@app.route('/staff/complete_trek/<int:trek_id>', methods=['POST'])
def complete_trek(trek_id):
    if 'user_id' not in session or session.get('user_role') != 'Staff':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    trek = Trek.query.filter_by(id=trek_id, assigned_staff_id=user_id).first_or_404()
    
    trek.status = 'Completed'
    bookings = Booking.query.filter_by(trek_id=trek_id).all()
    for b in bookings:
        b.status = 'Completed'
    db.session.commit()
    flash("Trek marked as completed.", "success")
    return redirect(url_for('staff_dashboard'))

@app.route('/staff/profile', methods=['GET', 'POST'])
def staff_profile():
    if 'user_id' not in session or session.get('user_role') != 'Staff':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))
        
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.contact_details = request.form.get('contact_details')
        new_password = request.form.get('password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        session['username'] = user.username
        flash("Profile updated successfully.", "success")
        return redirect(url_for('staff_dashboard'))
    return render_template('staff/profile.html', user=user)

@app.route('/staff/search')
def staff_search():
    if 'user_id' not in session or session.get('user_role') != 'Staff':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    query = request.args.get('q', '').lower()
    
    treks = Trek.query.filter(
        Trek.assigned_staff_id == user_id,
        (Trek.name.ilike(f'%{query}%') | Trek.location.ilike(f'%{query}%') | Trek.difficulty.ilike(f'%{query}%'))
    ).all()
    
    return render_template('staff/search_results.html', treks=treks, query=query)

# --- USER ROUTES ---
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'Trekker':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    open_treks = Trek.query.filter_by(status='Open').all()
    bookings = Booking.query.filter_by(trekker_id=user_id).all()
    return render_template('user/dashboard.html', open_treks=open_treks, bookings=bookings)

@app.route('/user/book/<int:trek_id>', methods=['POST'])
def book_trek(trek_id):
    if 'user_id' not in session or session.get('user_role') != 'Trekker':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    trek = Trek.query.get_or_404(trek_id)
    
    # Check if already booked
    existing_booking = Booking.query.filter_by(trekker_id=user_id, trek_id=trek_id).first()
    if existing_booking:
        flash("You have already booked this trek.", "warning")
        return redirect(url_for('user_dashboard'))
    
    if trek.status != 'Open':
        flash("This trek is not open for booking.", "danger")
        return redirect(url_for('user_dashboard'))
        
    num_spots = int(request.form.get('num_spots', 1))
    
    if num_spots <= 0:
        flash("Invalid number of spots.", "danger")
        return redirect(url_for('user_dashboard'))

    if trek.slots >= num_spots:
        booking = Booking(trekker_id=user_id, trek_id=trek_id, status='Booked', num_spots=num_spots)
        trek.slots -= num_spots
        db.session.add(booking)
        db.session.commit()
        flash(f"Successfully booked {num_spots} spot(s) for '{trek.name}'.", "success")
    else:
        flash("Not enough slots available.", "danger")
        
    return redirect(url_for('user_dashboard'))

@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session or session.get('user_role') != 'Trekker':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))
        
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.contact_details = request.form.get('contact_details')
        new_password = request.form.get('password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        session['username'] = user.username
        flash("Profile updated successfully.", "success")
        return redirect(url_for('user_dashboard'))
    return render_template('user/profile.html', user=user)

@app.route('/user/search')
def user_search():
    if 'user_id' not in session or session.get('user_role') != 'Trekker':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home'))

    query = request.args.get('q', '').lower()
    treks = Trek.query.filter(Trek.status == 'Open', (Trek.name.ilike(f'%{query}%') | Trek.location.ilike(f'%{query}%') | Trek.difficulty.ilike(f'%{query}%'))).all()
    return render_template('user/search_results.html', treks=treks, query=query)


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')
