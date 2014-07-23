from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from chores.models import ChoreSkeleton, Chore

class BasicForm(forms.ModelForm):
    class Meta:
        pass
    error_css_class = 'form_error'

class ChoreSkeletonForm(BasicForm):
    class Meta:
        model = ChoreSkeleton
        fields = ['short_name', 'short_description', 'point_value',
                  'start_time', 'end_time']

class ChoreForm(BasicForm):
    repeat_interval = forms.IntegerField(validators=[MinValueValidator(1)])
    number_of_repeats = forms.IntegerField(validators=[MinValueValidator(1)])
    class Meta:
        #TODO: maybe this shouldn't be a ModelForm if we're creating multiple
        #objects at once?
        model = Chore
        fields = ['skeleton', 'start_date', 'stop_date', 'repeat_interval',
                  'number_of_repeats']
        widgets = {
            field: forms.DateInput(attrs={'class': 'date_picker'})
            for field in ('start_date', 'stop_date')
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('stop_date') < cleaned_data.get('start_date'):
            # TODO: in Django 1.7 you can use `self.add_error()`. See
            # <https://docs.djangoproject.com/en/dev/ref/forms/api/
            # #django.forms.Form.add_error>.
            raise ValidationError('Stop date cannot be before start date.')
        return cleaned_data
