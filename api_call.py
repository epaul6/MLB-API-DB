import mlbstatsapi
from mongo_operations import insert_player_data, update_player_data, fetch_player_data
import aiohttp
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

logging.basicConfig(filename='mlb_fetcher.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLBStatsFetcher:
    def __init__(self):
        self.mlb = mlbstatsapi.Mlb()

    def get_player_ids_for_minor_leagues(self):
        # Initialize the MLB API client
        
        # Define the sport IDs for the minor leagues
        sport_ids = {
            # "AAA": 11,
            "AA": 12,
            # "A+": 13,
            # "A": 14
        }
        
        all_players = {}
        
        # Loop through each sport ID to get player data
        for league, sport_id in sport_ids.items():
            players = self.mlb.get_people(sport_id=sport_id, season=2023)
            player_data = {player.fullname: player.id for player in players}  # Dictionary with player name as key and ID as value
            all_players[league] = player_data

        return all_players

    def recursive_reformat(self, obj):
        if isinstance(obj, list):
            return [self.recursive_reformat(e) for e in obj]
        elif isinstance(obj, dict):
            return {k: self.recursive_reformat(v) for k, v in obj.items()}
        elif hasattr(obj, "__dict__"):
            return self.recursive_reformat(vars(obj))
        else:
            return obj

    async def fetch_stats_for_player(self, player_name, player_id, year):
        loop = asyncio.get_event_loop()

        def fetch():
            print(f'Fetching stats for {player_name}: {player_id}')
            return self.mlb.get_player_stats(person_id=player_id, stats=['season', 'career'], groups=['hitting', 'pitching'], season=year)
        

        with ThreadPoolExecutor() as pool:
            stats = await loop.run_in_executor(pool, fetch)

            stats = self.recursive_reformat(stats)

            insert_player_data(player_name, player_id, year, stats)  # Storing data in MongoDB
            logger.info(f'Added {player_name} to Mongo DB')
            return player_name, stats
    


    async def get_player_stats_for_year(self, player_data_dict, year):
        # Initialize the MLB API client
        all_player_stats = {}
        
        for league, players in player_data_dict.items():
            tasks = [self.fetch_stats_for_player(player_name, player_id, year) for player_name, player_id in players.items()]
            results = await asyncio.gather(*tasks)
            all_player_stats[league] = {player_name: stats for player_name, stats in results}
        
        return all_player_stats

if __name__ == "__main__":
    fetcher = MLBStatsFetcher()
    print("Grabbing Player Names: ID's")
    player_data_dict = fetcher.get_player_ids_for_minor_leagues()

    desired_year = 2023

    print("Received names/ID's. Grabbing stats for specified players...")
    asyncio.run(fetcher.get_player_stats_for_year(player_data_dict, desired_year))