from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.template import loader, Context

from profiles.models import UserProfile, GroupProfile, UserProfileForm
import datetime
import json

@login_required()
def index(response):
    coop = response.user.profile.coop
    coopers = coop.user_set.all().order_by('profile__first_name')
    # TODO: consider putting stewardship or any other info here. Consider also
    # any highlighting of self, presidents, etc.
    # contacts = sorted(map(lambda x: x.profile, coopers), key=lambda y:
                      # y.first_name)
    return render(response, 'profiles/index.html',
                  dictionary={'coop': coop, 'coopers': coopers})

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

@login_required()
# TODO: here and elsewhere, change the function parameter name to 'request'.
def profile_form(response):
    # TODO: this shouldn't ever be hit (POST hits `profile_edit`). Remove.
    if response.method == 'POST':
        form = UserProfileForm(response.POST)
        try:
            if form.is_valid():
                pass
            form.clean()
        except ValidationError as e:
            return HttpResponse('', reason=form.errors, status=999)
        # if form.is_valid():
            # # Make and save changes.
            # return HttpResponse('something here')
        # else:
            # return HttpResponse('something else')
    else:
        form = UserProfileForm(instance=response.user.profile)
    return render(response, 'profiles/profile_form.html', {'form': form})

def profile_edit(response):
    form = UserProfileForm(response.POST)
    # if form.is_valid():
        # print("it's valid")
    # else:
        # print("it isn't valid")
        # for field in form.errors:
            # print(' '.join(form.errors[field]))
    return HttpResponse(json.dumps({
        'errors': {
            field: ' '.join(form.errors[field]) for field in form.errors
        },
        'non_field_errors': list(form.non_field_errors())
    }), status=200)
