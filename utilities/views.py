from django.shortcuts import render

# Create your views here.

#TODO: this should be handled as a static page. Not sure how to get that
#working with templates.
def about(request):
    return render(request, 'utilities/about.html')
