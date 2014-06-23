from django.contrib.auth.models import User
import chores.views

indy = User.objects.all()[1]
list_obl = chores.views.get_obligations(indy)['list_information']
signed_up = list_obl[0]['sections'][0]
