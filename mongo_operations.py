from pymongo import MongoClient

client = MongoClient('localhost', 27017)

# Access the MLB database. Will be created if it doesn't exist
print('Connecting to Database...')
db = client.mlb_data

# Access the player_stats collection. Will be created if it doesn't exist
player_stats_collection = db.player_stats

def insert_player_data(player_name, player_id, year, stats):
	player_data = {
		'player_name': player_name,
		'player_id': player_id,
		'year': year,
		'stats': stats
	}
	player_stats_collection.insert_one(player_data)

def update_player_data(player_id, year, new_stats):
	query = {'player_id': player_id, 'year': year}
	new_values = {"$set": {'stats': new_stats}}
	player_stats_collection.update_one(query, new_values)

def fetch_player_data(player_id, year):
	query = {'player_id': player_id, 'year': year}
	return player_stats_collection.find_one(query)