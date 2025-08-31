from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Event, EventResponse, Lineup, LineupAssignment
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hockey_team.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        phone = request.form['phone']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(phone=phone).first():
            flash('Phone number already exists')
            return redirect(url_for('register'))
        
        user = User(username=username, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Ближайшие события
    upcoming_events = Event.query.filter(Event.datetime >= datetime.now()).order_by(Event.datetime.asc()).limit(5).all()
    
    # Ответы пользователя на события и информация о составе
    user_responses = {}
    user_lineups = {}
    for event in upcoming_events:
        response = EventResponse.query.filter_by(user_id=current_user.id, event_id=event.id).first()
        user_responses[event.id] = response.status if response else 'not_responded'
        
        # Проверяем, есть ли состав для этого события
        lineup = Lineup.query.filter_by(event_id=event.id).first()
        if lineup:
            # Проверяем, есть ли игрок в составе
            assignment = LineupAssignment.query.filter_by(lineup_id=lineup.id, user_id=current_user.id).first()
            if assignment:
                user_lineups[event.id] = {
                    'position': assignment.position,
                    'line': assignment.line
                }
    
    return render_template('dashboard.html', 
                         events=upcoming_events, 
                         user_responses=user_responses,
                         user_lineups=user_lineups)

@app.route('/events')
@login_required
def events():
    event_type = request.args.get('type', 'all')
    
    if event_type == 'games':
        events = Event.query.filter(Event.event_type == 'game').order_by(Event.datetime.desc()).all()
    elif event_type == 'trainings':
        events = Event.query.filter(Event.event_type == 'training').order_by(Event.datetime.desc()).all()
    else:
        events = Event.query.order_by(Event.datetime.desc()).all()
    
    return render_template('events.html', events=events, event_type=event_type)

@app.route('/event/<int:event_id>')
@login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    response = EventResponse.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    lineup = Lineup.query.filter_by(event_id=event_id).first()
    
    # Получаем все ответы на это событие
    responses = EventResponse.query.filter_by(event_id=event_id).all()
    
    return render_template('event_detail.html', 
                         event=event, 
                         user_response=response,
                         responses=responses,
                         lineup=lineup)

@app.route('/event/response', methods=['POST'])
@login_required
def event_response():
    event_id = request.form['event_id']
    status = request.form['status']
    comment = request.form.get('comment', '')
    
    event = Event.query.get_or_404(event_id)
    
    # Проверяем, не ответил ли уже пользователь
    existing_response = EventResponse.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    
    if existing_response:
        existing_response.status = status
        existing_response.comment = comment
        existing_response.responded_at = datetime.utcnow()
    else:
        response = EventResponse(
            user_id=current_user.id,
            event_id=event_id,
            status=status,
            comment=comment
        )
        db.session.add(response)
    
    db.session.commit()
    flash('Your response has been saved.')
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if current_user.role not in ['captain', 'admin']:
        flash('You do not have permission to create events.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_type = request.form['event_type']
        datetime_str = request.form['datetime']
        location = request.form['location']
        opponent = request.form.get('opponent', '')
        
        try:
            event_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid datetime format')
            return redirect(url_for('create_event'))
        
        event = Event(
            title=title,
            description=description,
            event_type=event_type,
            datetime=event_datetime,
            location=location,
            opponent=opponent if event_type == 'game' else None,
            created_by=current_user.id
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash('Event created successfully!')
        return redirect(url_for('events'))
    
    return render_template('create_event.html')

@app.route('/lineup/<int:event_id>')
@login_required
def lineup(event_id):
    if current_user.role not in ['captain', 'admin']:
        flash('You do not have permission to view lineups.')
        return redirect(url_for('dashboard'))
    
    event = Event.query.get_or_404(event_id)
    lineup = Lineup.query.filter_by(event_id=event_id).first()
    
    if not lineup:
        # Создаем пустой состав, если его нет
        lineup = Lineup(event_id=event_id, created_by=current_user.id)
        db.session.add(lineup)
        db.session.commit()
    
    # Получаем только тех игроков, которые отметились на это событие
    event_responses = EventResponse.query.filter_by(event_id=event_id, status='attending').all()
    attending_user_ids = [response.user_id for response in event_responses]
    
    # Игроки, которые отметились на событие
    players = User.query.filter(
        User.id.in_(attending_user_ids),
        User.is_active == True,
        User.role.in_(['player', 'captain'])
    ).order_by(User.last_name.asc(), User.first_name.asc()).all()
    
    # Назначения в составе
    assignments = LineupAssignment.query.filter_by(lineup_id=lineup.id).all()
    
    return render_template('lineup.html', 
                         event=event, 
                         lineup=lineup, 
                         players=players,
                         assignments=assignments)

@app.route('/update_lineup', methods=['POST'])
@login_required
def update_lineup():
    if current_user.role not in ['captain', 'admin']:
        return jsonify({'error': 'No permission'}), 403
    
    lineup_id = request.form['lineup_id']
    user_id = request.form['user_id']
    position = request.form['position']
    line = request.form.get('line', '')
    jersey_type = request.form.get('jersey_type', '')
    
    # Получаем состав и событие
    lineup = Lineup.query.get_or_404(lineup_id)
    event_id = lineup.event_id
    
    # Проверяем, отметился ли игрок на событие
    event_response = EventResponse.query.filter_by(
        event_id=event_id, 
        user_id=user_id, 
        status='attending'
    ).first()
    
    if not event_response:
        return jsonify({'error': 'Игрок должен отметить участие в событии перед назначением в состав'}), 400
    
    # Проверяем ограничения на вратарей
    if position == 'вратарь':
        existing_goalkeepers = LineupAssignment.query.filter_by(
            lineup_id=lineup_id, 
            position='вратарь'
        ).count()
        if existing_goalkeepers >= 2:
            return jsonify({'error': 'Максимум 2 вратаря в составе'}), 400
    
    # Автоматически определяем тип майки, если не указан
    if not jersey_type and position and line:
        if position == 'вратарь':
            jersey_type = 'goalkeeper'
        elif line in ['1', '2', '3']:
            jersey_type = 'white'
        elif line in ['4', '5', '6']:
            jersey_type = 'black'
    
    # Проверяем существующее назначение
    assignment = LineupAssignment.query.filter_by(lineup_id=lineup_id, user_id=user_id).first()
    
    if assignment:
        assignment.position = position
        assignment.line = line
        assignment.jersey_type = jersey_type
    else:
        assignment = LineupAssignment(
            lineup_id=lineup_id,
            user_id=user_id,
            position=position,
            line=line,
            jersey_type=jersey_type
        )
        db.session.add(assignment)
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    position = request.form.get('position', '')
    number = request.form.get('number')
    
    current_user.first_name = first_name if first_name else None
    current_user.last_name = last_name if last_name else None
    current_user.position = position if position else None
    if number:
        current_user.number = int(number)
    else:
        current_user.number = None
    
    db.session.commit()
    flash('Профиль обновлен успешно!')
    return redirect(url_for('profile'))

@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/update_role', methods=['POST'])
@login_required
def update_role():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    user_id = request.form['user_id']
    role = request.form['role']
    
    user = User.query.get(user_id)
    if user:
        user.role = role
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'User not found'}), 404

@app.route('/players')
@login_required
def players():
    """Страница со списком всех игроков команды"""
    # Получаем всех активных игроков, отсортированных по фамилии
    players = User.query.filter_by(is_active=True).filter(
        User.role.in_(['player', 'captain'])
    ).order_by(User.last_name.asc(), User.first_name.asc()).all()
    
    return render_template('players.html', players=players)

# Добавим обработку ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Создаем администратора по умолчанию, если его нет
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', phone='+79001234567', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=False)
