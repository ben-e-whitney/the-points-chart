$(document).ready(function() {
  $('.date_picker').datepicker();
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
  $.each(create_and_edit_args.concat(create_args), function(key, args) {
    var create_URL = '/'+args[1]+'/actions/create/'+args[2]+'/';
    $('#'+args[0]+'_create_form').submit(submit_function_creator(create_URL));
  });
  $.each(create_and_edit_args.concat(edit_args), function(key, args) {
    var edit_URL = '/'+args[1]+'/actions/edit/'+args[2]+'/';
    $('#'+args[0]+'_edit_form_selector').find('select').change(function() {
      var main_form = $('#'+args[0]+'_edit_form');
      //Get rid of the submit function. It's going to be added again later, so this
      //prevents it from being called multiple times then. Could probably be made smoother.
      main_form.unbind();
      main_form.empty();
      var choice_id = $(this).val();
      if (choice_id) {
        //TODO: add a class for the loading message. Failure message could go there, too.
        $(this).closest('tr').append("<td id='selector_loading_message'>Loading ...</td>");
        $.get(edit_URL, {choice_id: choice_id}, function (returnedData, textStatus, jqXHR) {
          //TODO: instead maybe we could first check whether the td is present, and so on.
          $('#selector_loading_message').remove();
          main_form.append(returnedData);
          $('#'+args[0]+'_edit_form').submit(submit_function_creator(edit_URL, choice_id));
        });
      }
    });
  });
});
