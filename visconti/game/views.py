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
    if localNetHost.exists() and models.get_host().phase == models.Phase.JOINING:
        context = {
            "isHost": False, 
            "hostIP": localNetHost.first().localIP,
        }
        return render(request, "gamescreen.html", context)
    else:
        return HttpResponse("No match started or match in progress!")

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
        if not models.get_players().filter(name=newName).exists():
            newPlayer = models.Player.objects.create(name=newName, current_bid=0)
            # newPlayer = models.Player.objects.create(name=newName, current_bid=0, lots="G10 g1 c2 d3 s5")
            newPlayer.save()
            models.advance_step()
            models.add_line_to_log(models.format_player_name(newName) + " joined!")
            return HttpResponse()
        return HttpResponse(status=403)

def start_match(request):
    if request.method == "POST":
        print("start")#start the game
        pCount = len(models.get_players())
        if pCount >= 3 and pCount <= 6:
            models.add_line_to_log("Match started.", True)
            models.start_day()
            models.advance_step()
            return HttpResponse()
        return HttpResponse(status=403)

def receive_choice(request):
    if request.method == "POST":
        name = request.POST["username"]
        drawOrBid = request.POST["drawOrBid"]
        host = models.get_host()
        if host.chooser == name:
            if drawOrBid == "true" and models.can_draw(): #draw
                models.add_to_group(models.draw_lot())
                models.advance_step()
                return HttpResponse()
            elif host.group_lots != "": #move to bidding
                models.end_choosing_phase()
                models.advance_step()
                return HttpResponse()
        return HttpResponse(status=403)

def receive_bid(request):
    if request.method == "POST":
        name = request.POST["username"]
        bid = int(request.POST["bid"])
        player = models.get_players().get(name=name)
        host = models.get_host()
        if host.bidder == name and (bid > models.highest_bid() or bid == 0) and bid <= player.money:
            player.current_bid = bid
            player.save()
            if (not bid == 0):
                models.add_line_to_log(models.format_player_name(player.name) + " bid " + models.format_money(bid) + ".")
            else:
                models.add_line_to_log(models.format_player_name(player.name) + " passed.")
        
            if (host.chooser == name or not models.is_remaining_bidder()): # chooser made last bid
                models.end_bidding_phase()
            else:
                models.move_to_next_bidder()
            models.advance_step()
            return HttpResponse()
        return HttpResponse(status=403)
    
def set_ready(request):
    if request.method == "POST":
        name = request.POST["username"]
        player = models.get_players().get(name=name)
        player.ready = True
        player.save()
        if models.get_players().exclude(ready=True).count() == 0: #all players are ready
            models.end_waiting_phase()
            models.advance_step()
        return HttpResponse()

def delete_data():
    query = models.Host.objects.all()
    if query.exists():
        query.delete()
    query = models.Player.objects.all()
    if query.exists():
        query.delete()
