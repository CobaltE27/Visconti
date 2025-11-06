from django.shortcuts import render, redirect, reverse
import socket
from . import models
from . import aiplayer
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

    return redirect(reverse("load_match") + "?hosting=1")

def join_match(request):
    return redirect(reverse("load_match") + "?hosting=0")
    
def load_match(request):
    if request.method == "GET":
        hosting = request.GET.get("hosting", "0") == "1"
        localNetHost = models.Host.objects.all()
        if localNetHost.exists() and models.get_host().phase == models.Phase.JOINING:
            context = {
                "isHost": hosting, 
                "hostIP": localNetHost.first().localIP,
                "aiDictionary": aiplayer.aiDictionary,
            }
            return render(request, "gamescreen.html", context)
        else:
            return HttpResponse("No match started or match in progress!")
    if request.method == "POST":
        action = request.POST["action"]
        if action == "data":
            return data()
        elif action == "setname":
            return set_name(request.POST["name"], request.POST.get("ai", ""))
        elif action == "start":
            return start_match()
        elif action == "choose":
            return receive_choice(request.POST["username"], str(request.POST["drawOrBid"]).lower() == "true")
        elif action == "bid":
            return receive_bid(request.POST["username"], int(request.POST["bid"]))
        elif action == "ready":
            return set_ready(request.POST["username"])
        return HttpResponse(status=403)

def data():
    dataDict = data_to_dict()
    return HttpResponse(json.dumps(dataDict), content_type="application/json")

def set_name(newName: str, ai: str = ""):
    if not models.get_players().filter(name=newName).exists():
        newPlayer = models.Player.objects.create(name=newName, current_bid=0, ai=ai, ready=(False if ai == "" else True))
        newPlayer.save()
        models.advance_step()
        models.add_line_to_log(models.format_player_name(newName) + (" joined!" if ai == "" else " was added!"))
        return HttpResponse()
    elif ai != "":
        counter = 0
        modifiedName = newName + str(counter)
        while (models.get_players().filter(name=modifiedName).exists()):
            counter += 1
            modifiedName = newName + str(counter)
        newPlayer = models.Player.objects.create(name=modifiedName, current_bid=0, ai=ai, ready=True)
        newPlayer.save()
        models.advance_step()
        models.add_line_to_log(models.format_player_name(newName) + " was added!")
        return HttpResponse()
    return HttpResponse(status=403)

def start_match():
    print("start")#start the game
    pCount = len(models.get_players())
    if pCount >= 3 and pCount <= 6:
        models.add_line_to_log("Match started.", True)
        models.start_day()
        models.advance_step()
        return HttpResponse()
    return HttpResponse(status=403)

def receive_choice(name: str, draw: bool ):
    host = models.get_host()
    if host.chooser == name:
        if draw and models.can_draw(): #draw
            models.add_to_group(models.draw_lot())
            models.advance_step()
            return HttpResponse()
        elif host.group_lots != "": #move to bidding
            models.end_choosing_phase()
            models.advance_step()
            return HttpResponse()
        return HttpResponse(status=403)
    return HttpResponse(status=403)

def receive_bid(name: str, bid: int):
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
    
def set_ready(name: str):
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

def model_to_dict(queryResult):
    return json.loads(serializers.serialize("json", queryResult))

def data_to_dict():
    players = models.get_players()
    host = models.Host.objects.all()
    dataDict = {
        "players": model_to_dict(players),
        "host": model_to_dict(host),
        }
    return dataDict

def test_match(request):
    if request.method == "GET":
        ais = request.GET.get("p", None)
        trials = int(request.GET.get("tc", "1"))
        if not ais:
            return HttpResponse(status=400)
        ais = ais.split()
        winners = []
        localNetAddr = socket.gethostbyname(socket.gethostname())
        for c in range(0, trials):
            delete_data()
            newHost = models.Host.objects.create(localIP=localNetAddr)
            print("hostid: " + str(newHost.id))
            newHost.save()
            for ai in ais:
                set_name(ai, ai)
            start_match()
            winners.append(models.get_players().order_by("-money").first().name + " ")
        return HttpResponse(str(winners))

