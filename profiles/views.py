from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.template import loader, Context
from profiles.models import UserProfile, GroupProfile
import datetime

@login_required()
def index(response):
    coop = response.user.get_profile().coop
    coopers = coop.user_set.all()
    # TODO: consider putting stewardship or any other info here. Consider also
    # any highlighting of self, presidents, etc.
    contacts = sorted(map(lambda x: x.get_profile(), coopers), key=lambda y:
                      y.first_name)
    return render(response, 'profiles/index.html',
                  dictionary={'coop': coop, 'contacts': contacts})

# TODO: try getting it exported as a PDF.
@login_required()
def export(response):
    coop = response.user.get_profile().coop
    coopers = coop.user_set.all()
    contacts = sorted(map(lambda x: x.get_profile(), coopers), key=lambda y:
                      y.first_name)
    contacts.remove(response.user.get_profile())
    # Here we are assuming that the site is using the UTC timezone.
    # TODO: check if this works as you are expecting.
    current_time = datetime.datetime.now().isoformat()\
        .replace('-', '').replace(':', '')+'Z'
    response = HttpResponse(content_type='text/vcard')
    response['Content-Disposition'] = ('attachment; '
        'filename="{sho}_contacts.vcf"'.format(
            sho=coop.profile.short_name.replace(' ', '_')))
    template = loader.get_template('profiles/contacts.vcf')
    # TODO: this seems to be working fine. Return to it when you better
    # understand when to use RequestContext.
    context = Context({'coop': coop, 'contacts': contacts,
                       'current_time': current_time})
    response.write(template.render(context))
    return response
