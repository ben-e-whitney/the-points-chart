from stewardships.models import (StewardshipSkeleton, Stewardship, Absence,
    ShareChange)
from stewardships.forms import (ClassicalStewardshipSkeletonForm,
    ClassicalStewardshipFormCreator, SpecialPointsFormCreator, LoanFormCreator,
    AbsenceFormCreator, ShareChangeFormCreator)

from utilities.AJAX import create_function_creator, edit_function_creator

classical_stewardship_skeleton_create = create_function_creator(
    model=StewardshipSkeleton,
    model_form=ClassicalStewardshipSkeletonForm
)
classical_stewardship_create = create_function_creator(
    model=Stewardship,
    model_form_callable=ClassicalStewardshipFormCreator
)
loan_create = create_function_creator(
    model=Stewardship,
    model_form_callable=LoanFormCreator
)
special_points_create = create_function_creator(
    model=Stewardship,
    model_form_callable=SpecialPointsFormCreator
)
absence_create = create_function_creator(
    model=Absence,
    model_form_callable=AbsenceFormCreator
)
share_change_create = create_function_creator(
    model=ShareChange,
    model_form_callable=ShareChangeFormCreator
)

classical_stewardship_skeleton_edit = edit_function_creator(
    model=StewardshipSkeleton,
    model_form=ClassicalStewardshipSkeletonForm
)
classical_stewardship_edit = edit_function_creator(
    model=Stewardship,
    model_form_callable=ClassicalStewardshipFormCreator
)
loan_edit = edit_function_creator(
    model=Stewardship,
    model_form_callable=LoanFormCreator
)
special_points_edit = edit_function_creator(
    model=Stewardship,
    model_form_callable=SpecialPointsFormCreator
)
absence_edit = edit_function_creator(
    model=Absence,
    model_form_callable=AbsenceFormCreator
)
share_change_edit = edit_function_creator(
    model=ShareChange,
    model_form_callable=ShareChangeFormCreator
)