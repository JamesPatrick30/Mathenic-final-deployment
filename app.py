from flask import Flask , request
from flask_socketio import SocketIO, join_room, emit, leave_room
from flask_cors import CORS
import uuid
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app,cors_allowed_origins="*")

rooms = {}
message = 'hello from python'


@socketio.on('create_lobby')
def create_room(data):
    room_id = str(uuid.uuid4())[0:6]
    Questions = data['noOFquestion']
  
    operation = data['operation']
    hostid = request.sid
    timer = data['time']
    lobbykey =str(uuid.uuid4())[0:9]
   # requestid = request.aid
    while room_id in rooms:
        room_id = str(uuid.uuid4())[0:6]

    rooms[room_id] ={
        'Lobby_key': lobbykey,
        'Number_of_Questions' : Questions,
        'host': hostid,
        'players' : [],
        'operation' : operation,
        'timer' : timer,
        'gamestatus' : False

    }
    emit('room_created',{'roomid':room_id,'roomkey' : lobbykey},to = hostid)
    #emit('allertme','created',to = request.sid)
    #emit('error',str( request.sid) ,to= request.sid)
         
@socketio.on('join_room')
def handle_join_room(data):
    usermname = data['username']
    room_id = data['room_id']
    

    if room_id in rooms:
        user_id = str(uuid.uuid4())[0:6]
        user_sid = request.sid
        while user_id in rooms[room_id]['players']:
            user_id = str(uuid.uuid4())[0:6]
            
        join_room (room_id)
        rooms[room_id]['players'].append( {
        'player_id' : user_id,
        'username' :usermname,
        'score' : 0,
        'status' : False,
        'user_sid' : user_sid
        })
        emit('Room_Update',  rooms[room_id]['players'],to = rooms[room_id]['host'])
        emit('userJoined',user_id,to =user_sid )
        
            
        for user in rooms[room_id]['players']:
            emit('Room_update', rooms[room_id]['players'] ,to = user['user_sid'])
        
        if rooms[room_id]['gamestatus'] == True:
             emit('gamestart',{'operation' : rooms[room_id]['operation'],'time' : rooms[room_id]['timer'],'numberOfQuestion':rooms[room_id]['Number_of_Questions']},to = user_sid)
        
    else:
        emit('error','the looby dosn\'t exist' ,to= request.sid)

@socketio.on('start_game')
def handle_gamesatart(data):
    roomid = data['roomid']
    roomkey = data['roomkey']

    if roomid in rooms:
        if roomkey == rooms[roomid]['Lobby_key']:
            rooms[roomid]['gamestatus'] = True
            for player in rooms[roomid]['players']:
                emit('gamestart',{'time' : rooms[roomid]['timer'],'operation' :rooms[roomid]['operation'],'numberOfQuestion' : rooms[roomid]['Number_of_Questions']},to = player['user_sid'])
                
            emit('alerthost_gamestarted',to = rooms[roomid]['host'])
        else:
            emit('error','you dont have the right key',to = request.sid)

    else:
        emit('error','room doesn\'t exist',to = request.sid)





@socketio.on('score_update')
def handle_score_update(data):
    roomId = data['room_id']
    userid = data['userid']
    user_sid = request.sid
    userscore = data['score']
    if roomId in rooms:
        for user in rooms[roomId]['players']:
            if user['player_id'] == userid :
                user['score'] = userscore
                user['status'] = True
                emit('Update_score',user,to= rooms[roomId]['host'] )
                break
    
        
    else:
        emit('error','the lobby doesn\'t exist', to = user_sid)
    

@socketio.on('accidental_reload')
def handle_reload(data):
    playerid = data['playerid']
    roomid = data['roomid']
    player_sid = request.sid

    if roomid in rooms:
        for player in rooms[roomid]['players'] :
            if player['player_id'] == playerid:
                player['user_sid'] = player_sid
                if player['status'] == True and rooms[roomid]['gamestatus']== True:
                    emit('showscore',player['score'],to = player_sid)
                elif player['status'] == False and rooms[roomid]['gamestatus']== True:
        
                    emit('gamestart',{'operation' : rooms[roomid]['operation'],'time' : rooms[roomid]['timer'],'numberOfQuestion':rooms[roomid]['Number_of_Questions']},to = player_sid)

                else:
                     emit('Room_update', rooms[roomid]['players'] ,to = player_sid)
                
    else:
        emit('error','room doesn\'t exist ar',to = player_sid)

@socketio.on('handle_ar_host')
def Handle_areload_host(data):
    roomid = data['roomid']
    roomkey = data['roomkey']

    if roomid in rooms:
        if roomkey == rooms[roomid]['Lobby_key']:
            rooms[roomid]['host'] = request.sid
            if rooms[roomid]['gamestatus'] == False:
                emit('room_created',{'roomid':roomid,'roomkey' : roomkey},to = rooms[roomid]['host'])
                emit('Room_Update',  rooms[roomid]['players'],to = rooms[roomid]['host'])
            else:
                emit('Room_Update',  rooms[roomid]['players'],to = rooms[roomid]['host'])
                for player in rooms[roomid]['players']:
                    if player['status'] == True:
                        emit('alerthost_gamestarted',to = rooms[roomid]['host'])
                        emit('Update_score',player,to= rooms[roomid]['host'] )

        else:
            emit('error','room doesn\'t exist ar',to = request.sid)
    else:
        emit('error','room doesn\'t exist ar',to = request.sid)
                        
@socketio.on('leaveroom')
def handle_player_leave(data):
    roomId = data['room_id']
    userid = data['userid']
    if roomId in rooms:
        for player in rooms[roomId]['players']:
            if userid == player['player_id']: 
                rooms[roomId]['players'] = [p for p in rooms[roomId]['players'] if p['player_id'] != userid]
                emit('Room_Update',  rooms[roomId]['players'],to = rooms[roomId]['host'])
                for player1 in rooms[roomId]['players']:
                    emit('Room_update',  rooms[roomId]['players'],to = player1['user_sid'])

            else:
                emit('error','you didn\'t enter the room',to = request.sid)
        
        

    else:
         emit('error','room doesn\'t exist',to = request.sid)

@socketio.on('delete_room')
def handle_room_delete(data):
    roomid = data['roomid']
    roomkey = data['roomkey']

    if roomid in rooms :
        if roomkey == rooms[roomid]['Lobby_key']:
            del rooms[roomid]
            emit('error','the room is successfully deleted',to = request.sid)
        else:
            emit('error','you dont have the correct key',to = request.sid)

    else: 
       emit('error','room doesn\'t exist',to = request.sid) 

@socketio.on('connection')
def checkconnection():
    print('client connected')
    socketio.emit('message',message)

@socketio.on('client_message')
def handle_message(data):
    print(f"Received message : {data}")
    socketio.emit('messsage',f"server received :{data}")

@app.route('/api/lobbies')
def alldata():
    return rooms

@socketio.on('connection')
def handle_score_update(data):
     emit('connection','connected to backend',to = request.sid) 

@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    return response


if __name__ == '__main__':
    socketio.run(app, debug=True,port=2000)