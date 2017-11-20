from django.db import models
from django.contrib.auth.models import User



class Team(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name


class Member(models.Model):
    name = models.CharField(max_length=200)
    avatar = models.CharField(blank=True, max_length=200)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True)
    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=200)
    estimated_hours = models.IntegerField()
    members = models.ManyToManyField(Member, through='Membership')
    def __str__(self):
        return self.name


class Membership(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
