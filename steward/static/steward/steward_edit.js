$(document).ready(function() {
  $('.date_picker').datepicker({dateFormat: 'yy-mm-dd'});
  //TODO: activate once you have 'particulars' section up.
  //$('#coop_overview').accordion({active: 0, collapsible: true,
                                //heightStyle: 'content', animate: false});
  $.each(['creating', 'editing'], function(index, type) {
    $('#'+type+'_forms').accordion({active: false, collapsible: true,
                                    heightStyle: "content", animate: false});
  });
  $('#outer_accordion').accordion({active: 0, collapsible: true,
    heightStyle: "content", animate: false});
  var create_and_edit_args = [
    ['chore_skeleton', 'chores', 'chore_skeleton'],
    ['chore', 'chores', 'chore'],
    ['classical_stewardship_skeleton', 'stewardships',
      'classical_stewardship_skeleton'],
    ['classical_stewardship', 'stewardships', 'classical_stewardship'],
    ['special_points', 'stewardships', 'special_points'],
    ['loan', 'stewardships', 'loan'],
    ['absence', 'stewardships', 'absence'],
    ['share_change', 'stewardships', 'share_change'],
    ['user', 'steward', 'user'],
  ];
  var create_args = [];
  var edit_args = [
    ['group_profile', 'steward', 'group_profile'],
  ];
  $.each(create_and_edit_args.concat(create_args), configure_create_form);
  $.each(create_and_edit_args.concat(edit_args), configure_edit_form);
});
