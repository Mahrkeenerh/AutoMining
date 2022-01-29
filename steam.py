import requests


def request(method, url):

    session = requests.Session()

    return session.request(method, url).json()


def get_player_summaries(key, id):

    return request('GET', 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=' + key + '&steamids=' + id)
