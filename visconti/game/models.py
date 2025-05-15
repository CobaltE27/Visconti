from django.db import models

# Create your models here.
class Host(models.Model):
    localIP = models.CharField(max_length=20)

class Player(models.Model):
    name = models.CharField(max_length=100)
    money = models.IntegerField(default=40)