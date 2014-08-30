from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from steward.forms import UserFormCreator
from utilities.AJAX import (make_form_response, create_function_creator,
    edit_function_creator)

user_create = create_function_creator(
    model=User,
    model_form_callable=UserFormCreator
)
user_edit = edit_function_creator(
    model=User,
    model_form_callable=UserFormCreator
)
