from django.db import models
from django.contrib.auth.models import User



class Team(models.Model):
    name = models.CharField(max_length=200)


class Member(models.Model):
    name = models.CharField(max_length=200)
    avatar = models.CharField(blank=True, max_length=200)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User)


class Project(models.Model):
    name = models.CharField(max_length=200)
    estimated_hours = models.IntegerField()
    members = models.ManyToManyField(Member, through='Membership')


class Membership(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
