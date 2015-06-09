$(document).ready(function() {
  $('.date_picker').datepicker({dateFormat: 'yy-mm-dd'});
  $('#creating_forms').accordion({
    active: false,
    collapsible: true,
    heightStyle: "content",
    animate: false
  });
  $.each([
    new functionCreators.FormSubmitter('ChoreSkeleton', 'chores', 'chore_skeleton'),
    new functionCreators.FormSubmitter('Chore', 'chores', 'chore'),
    new functionCreators.FormSubmitter(
      'StewardshipSkeleton',
      'stewardships',
      'classical_stewardship_skeleton'
    ),
    new functionCreators.FormSubmitter('Stewardship', 'stewardships', 'classical_stewardship'),
    new functionCreators.FormSubmitter('SpecialPointsGrant', 'stewardships', 'special_points'),
    new functionCreators.FormSubmitter('Loan', 'stewardships', 'loan'),
    new functionCreators.FormSubmitter('Absence', 'stewardships', 'absence'),
    new functionCreators.FormSubmitter('ShareChange', 'stewardships', 'share_change'),
    new functionCreators.FormSubmitter('User', 'steward', 'user'),
  ], functionCreators.configureCreateForm);
});
