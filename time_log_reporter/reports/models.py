from django.db import models
from django.contrib.auth.models import User



class Team(models.Model):
    name = models.CharField(max_length=200)
    admin = models.ForeignKey(User)
    def __str__(self):
        return self.name


class Member(models.Model):
    name = models.CharField(max_length=200)
    avatar = models.CharField(blank=True, max_length=200)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=200)
    estimated_hours = models.IntegerField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects')
    members = models.ManyToManyField(Member, through='Membership')
    def __str__(self):
        return self.name


class Membership(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='memberships')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    def __str__(self):
        return ''