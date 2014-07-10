from django import forms

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
    class Meta:
        model = Chore
        fields = ['skeleton', 'start_date', 'stop_date']
        widgets = {
            field: forms.DateInput(attrs={'class': 'date_picker'})
            for field in ('start_date', 'stop_date')
        }

    def clean(self):
        # TODO: just return this expression?
        cleaned_data = super().clean()
        if cleaned_data.get('stop_date') < cleaned_data.get('start_date'):
            # TODO: in Django 1.7 you can use `self.add_error()`. See
            # <https://docs.djangoproject.com/en/dev/ref/forms/api/
            # #django.forms.Form.add_error>.
            raise ValidationError('Stop date cannot be before start date.')
        return cleaned_data
