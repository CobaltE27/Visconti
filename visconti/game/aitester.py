import requests
import re

def main():
    players = ["gian", "errata", "randy"]
    trials = 50
    results = requests.get("http://10.0.0.7:8000/test/?p=" + " ".join(players) + "&tc=" + str(trials)).text
    print(results)

if __name__ == "__main__":
    main()