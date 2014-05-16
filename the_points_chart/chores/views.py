from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse

def index(response):
    return HttpResponse('Welcome to the points chart.')

def description(response, chore_id):
    return HttpResponse('Here is the description for chore ' 
                        '{cid}.'.format(cid=chore_id))

