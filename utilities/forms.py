from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH

class BasicForm(forms.ModelForm):

    '''
    Subclass of forms.ModelForm. Adds `error_css_class` class variable and
    extends `save` method to handle 'request' keyword argument.

    Public methods:
        save
    '''

    class Meta:
        pass

    error_css_class = 'form_error'

    def save(self, *args, **kwargs):
        '''
        Extends forms.ModelForm.save, allowing for 'request' keyword.

        'request' keyword argument is thrown away if present.
        '''
        return super().save(
            *args,
            **{key: value for key, value in kwargs.items() if key != 'request'}
        )

def cycle_field_creator(coop):
    '''
    Find `coop`'s cycles and return a form field with those cycles as choices.

    Arguments:
        coop -- Group whose cycles we are interested in.

    Return a CharField with the current cycles as choices. No initial or
    default choice is made.
    '''
    CYCLE_CHOICES = tuple(
        (int(cycle_num), 'Cycle {num} ({stadat} to {stodat})'
             .format(num=cycle_num, stadat=cycle_start.isoformat(),
                     stodat=cycle_stop.isoformat()))
        for cycle_num, cycle_start, cycle_stop in coop.profile.cycles()
    )
    #I have found no way to set a default (not just initial) value. See
    #<https://docs.djangoproject.com/en/dev/ref/forms/fields/#initial>.
    return forms.CharField(widget=forms.Select(choices=CYCLE_CHOICES))

def cooper_field_creator(coop, blank=False, required=True):
    '''
    Find `coop`'s members and return a form field with those people as choices.

    Arguments:
        coop -- Group whose members we are interested in.

    Keyword arguments:
        blank -- If True, a blank choice is added to the form field. If False,
            no action is taken.
        required -- Passed as a keyword argument to CharField constructor.

    Return a CharField with the current members as choices. No initial or
    default choice is made.
    '''
    COOPER_CHOICES = [
        (cooper.id, cooper.profile.nickname)
        for cooper in coop.user_set.all().prefetch_related('profile').order_by(
            'profile__nickname')
    ]
    if blank:
        COOPER_CHOICES = BLANK_CHOICE_DASH+COOPER_CHOICES
    cooper = forms.CharField(required=required,
                             widget=forms.Select(choices=COOPER_CHOICES))
    return cooper

