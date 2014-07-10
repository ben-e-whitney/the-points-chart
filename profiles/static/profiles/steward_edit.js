$(document).ready(function() {
  $('.date_picker').datepicker();
  $('#form_accordion').accordion({active: false, collapsible: true,
    heightStyle: "content"});
  var chores_create_URL = '/chores/actions/create/';
  var stewardships_create_URL = '/stewardships/actions/create/';
  var ids_and_URLs = [
    ['chore_skeleton_form', chores_create_URL+'chore_skeleton/'],
    ['chore_form', chores_create_URL+'chore/'],
    ['classical_stewardship_skeleton_form',
     stewardships_create_URL+'classical_stewardship_skeleton/'],
    ['classical_stewardship_form',
      stewardships_create_URL+'classical_stewardship/'],
    ['special_points_form', stewardships_create_URL+'special_points/'],
    ['loan_form', stewardships_create_URL+'loan/'],
    ['absence_form', stewardships_create_URL+'absence/'],
    ['share_change_form', stewardships_create_URL+'share_change/'],
  ];
  ids_and_URLs.forEach(function(args) {
    $('#'+args[0]).submit(submit_function_creator(args[1]));
  });
});
