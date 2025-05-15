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

def join_match(request, match_num):
    localNetHost = models.Host.objects.filter(id=match_num)
    if localNetHost.exists():
        print(localNetHost.first().localIP)

        context = {
            "isHost": False, 
            "hostIP": localNetHost.first().localIP,
            "matchNum": match_num,
        }
        return render(request, "gamescreen.html", context)
    else:
        return HttpResponse("Bad match number! Make sure you entered the right url.")

def data(request):
    players = models.Player.objects.all()
    dataJson = {"players": serializers.serialize("json", players)}
    return HttpResponse(json.dumps(dataJson), content_type="application/json")

def set_name(request):
    if request.method == "POST":
        newName = request.POST["name"]
        newPlayer = models.Player.objects.create(name=newName)
        newPlayer.save()
        return HttpResponse()

def delete_data():
    query = models.Host.objects.all()
    if query.exists():
        query.delete()
    query = models.Player.objects.all()
    if query.exists():
        query.delete()