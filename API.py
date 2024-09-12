from flask import Flask, request, jsonify
import json

app = Flask(__name__)

leaderboard_data = []

AUTH_KEY = "YourAPIKey"  # To update api use /leaderboard?auth=YourAPIKey on POST

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    return jsonify(leaderboard_data)

@app.route('/leaderboard', methods=['POST'])
def update_leaderboard():
    global leaderboard_data
    auth_key = request.args.get('auth')
    
    if auth_key != AUTH_KEY:
        return 'Unauthorized', 403

    print("Request Headers:")
    for header, value in request.headers.items():
        print(f"{header}: {value}")

    print("Raw Body Data:")
    raw_data = request.data
    print(raw_data)
    
    try:
        decoded_data = raw_data.decode('utf-8')
        print("Decoded Body Data:")
        print(decoded_data)
        data = json.loads(decoded_data)
    except Exception as e:
        print(f"Error: {e}")
        return 'Invalid JSON or Content-Type not set to application/json', 400
    
    print("Parsed JSON Data:", data)
    
    for team in data['leaderboard']:
        if team['teamName'] == "Team Yellow":
            team['teamName'] = "Team Orange"
            team['teamNumber'] = 5
        elif team['teamName'] == "Team Orange":
            team['teamName'] = "Team Yellow"
            team['teamNumber'] = 4
    
    if data['winningTeam']['teamName'] == "Team Yellow":
        data['winningTeam']['teamName'] = "Team Orange"
        data['winningTeam']['teamNumber'] = 5
    elif data['winningTeam']['teamName'] == "Team Orange":
        data['winningTeam']['teamName'] = "Team Yellow"
        data['winningTeam']['teamNumber'] = 4
    
    leaderboard_data = data
    
    print("Updated Leaderboard Data:", leaderboard_data)
    
    return 'Leaderboard Updated Successfully!', 200
