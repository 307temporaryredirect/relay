from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_room')
def on_join(data):
    room = data['room']
    username = data['username']
    team = data['team']
    role = data.get('role', 'player')
    join_room(room)
    if room not in rooms_data:
        rooms_data[room] = {'teams': {}, 'relay_images': {}, 'current_turn': {}, 'round': 1, 'moderator': None, 'points': {}}
    if role == 'moderator':
        rooms_data[room]['moderator'] = username
    else:
        if team not in rooms_data[room]['teams']:
            rooms_data[room]['teams'][team] = []
            rooms_data[room]['relay_images'][team] = []
            rooms_data[room]['current_turn'][team] = None
            rooms_data[room]['points'][team] = 0
        rooms_data[room]['teams'][team].append(username)
    emit('joined_room', {'msg': f"{username} joined room {room} as team {team}"}, room=room)

@socketio.on('send_drawing')
def handle_send_drawing(data):
    room = data['room']
    team = data['team']
    username = data['username']
    image_data = data['image']
    rooms_data[room]['relay_images'][team].append(image_data)
    players = rooms_data[room]['teams'][team]
    current_index = players.index(username)
    next_index = (current_index + 1) % len(players)
    next_player = players[next_index]
    rooms_data[room]['current_turn'][team] = next_player
    emit('receive_drawing', {'image': image_data, 'next_player': next_player}, room=room)

@socketio.on('manual_score')
def handle_manual_score(data):
    room = data['room']
    team = data['team']
    points = data['points']
    rooms_data[room]['points'][team] += points
    emit('update_score', {'team': team, 'total_points': rooms_data[room]['points'][team]}, room=room)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
