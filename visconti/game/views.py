from django.shortcuts import render, redirect
import socket
from . import models
from django.http import HttpResponse
import json
from django.core import serializers

# Create your views here.
def host_match(request):
    localNetAddr = socket.gethostbyname(socket.gethostname())
    delete_data()
    newHost = models.Host.objects.create(localIP=localNetAddr)
    print("hostid: " + str(newHost.id))
    newHost.save()

    context = {
            "isHost": True, 
            "hostIP": newHost.localIP,
            "matchNum": newHost.id,
        }
    return render(request, "gamescreen.html", context)

def join_match(request):
    localNetHost = models.Host.objects.all()
    if localNetHost.exists():
        print(localNetHost.first().localIP)

        context = {
            "isHost": False, 
            "hostIP": localNetHost.first().localIP,
        }
        return render(request, "gamescreen.html", context)
    else:
        return HttpResponse("No match started!")

def data(request):
    players = models.get_players()
    host = models.Host.objects.all()
    dataJson = {
        "players": model_to_dict(players),
        "host": model_to_dict(host),
        }
    return HttpResponse(json.dumps(dataJson), content_type="application/json")

def model_to_dict(queryResult):
    return json.loads(serializers.serialize("json", queryResult))


def set_name(request):
    if request.method == "POST":
        newName = request.POST["name"]
        # newPlayer = models.Player.objects.create(name=newName, current_bid=0, lots="G10 g1 c2 d3 s4 f5")
        newPlayer = models.Player.objects.create(name=newName, current_bid=0)
        newPlayer.save()
        return HttpResponse()

def start_match(request):
    if request.method == "POST":
        print("start")#start the game
        pCount = len(models.get_players())
        if pCount >= 3 and pCount <= 6:
            models.start_day()

def receive_choice(request):
    if request.method == "POST":
        name = request.POST["username"]
        drawOrBid = bool(request.POST["drawOrBid"])
        host = models.get_host()
        if host.chooser == name:
            if drawOrBid and models.can_draw(): #draw
                models.add_to_group(models.draw_lot())
                host.save()
            else: #move to bidding
                models.end_choosing_phase()

    return HttpResponse()

def receive_bid(request):
    if request.method == "POST":
        name = request.POST["username"]
        bid = int(request.POST["bid"])
        player = models.get_players().get(name=name)
        host = models.get_host()
        if host.bidder == name:
            player.current_bid = bid
            player.save()
        
            if (host.chooser == name): # chooser made last bid
                models.end_bidding_phase()
            else:
                models.move_to_next_bidder()
    return HttpResponse()

def delete_data():
    query = models.Host.objects.all()
    if query.exists():
        query.delete()
    query = models.Player.objects.all()
    if query.exists():
        query.delete()
