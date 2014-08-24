from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH

class BasicForm(forms.ModelForm):
    class Meta:
        pass
    error_css_class = 'form_error'

    #TODO: think this is because you're passing everything requests. Check.
    def save(self, *args, **kwargs):
        print('in BasicForm.save')
        print('args: {arg}'.format(arg=args))
        print('kwargs: {kwa}'.format(kwa=kwargs))
        return super().save(*args,
                            **{key: value for key, value in kwargs.items()
                               if key != 'request'})

def cycle_field_creator(coop):
    CYCLE_CHOICES = tuple(
        (int(cycle_num), 'Cycle {num} ({stadat} to {stodat})'
             .format(num=cycle_num, stadat=cycle_start.isoformat(),
                     stodat=cycle_stop.isoformat()))
        for cycle_num, cycle_start, cycle_stop in coop.profile.cycles()
    )
    # TODO: figure out if default is allowed here, or how to do it.
    cycle = forms.CharField(widget=forms.Select(choices=CYCLE_CHOICES))
    return cycle

def cooper_field_creator(coop, blank=False, required=True):
    COOPER_CHOICES = [(cooper.id, cooper.profile.nickname) for cooper in
                           coop.user_set.all()]
    if blank:
        COOPER_CHOICES = BLANK_CHOICE_DASH+COOPER_CHOICES
    cooper = forms.CharField(required=required,
                             widget=forms.Select(choices=COOPER_CHOICES))
    return cooper

