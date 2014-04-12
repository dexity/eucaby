
from django.db import models
from django.contrib.auth.models import User

class UserLocation(models.Model):
    user = models.ForeignKey(User)
    lat  = models.CharField(max_length=50)
    lng  = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)

