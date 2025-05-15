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
        newPlayer = models.Player.objects.create(name=newName)
        newPlayer.save()
        return HttpResponse()

def start_match(request):
    if request.method == "POST":
        print("start")#start the game
        pCount = len(models.get_players())
        if pCount >= 3 and pCount <= 6:
            models.start_day()

def delete_data():
    query = models.Host.objects.all()
    if query.exists():
        query.delete()
    query = models.Player.objects.all()
    if query.exists():
        query.delete()
