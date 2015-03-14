var report_form_finish = function(form, icon_URL, icon_description, non_field_errors) {
  var form_status = form.find('.form_status');
  form_status.empty();
  if (non_field_errors == undefined) {
    non_field_errors = '';
  }
  //This should be the same as settings.STATIC_URL.
  var STATIC_URL = '/static/'
  var status = '<object data="'+STATIC_URL+icon_URL+'">'+icon_description+'</object>';
  if (non_field_errors != undefined) {
    status += ' '+non_field_errors;
  }
  form_status.append(status);
  form.find('.submit_button').prop('disabled', false);
  return null;
};

var report_success_creator = function(form) {
  var report_success = function(returnedData, textStatus, jqXHR) {
    var icon_URL = 'icons/checkmark.svg';
    var icon_description = 'checkmark';
    var form_status = form.find('.form_status');
    report_form_finish(form, icon_URL, icon_description);
    return null;
  };
  return report_success;
};

var report_errors_creator = function(form) {
  var report_errors = function(returnedData, textStatus, jqXHR) {
    responseText = JSON.parse(returnedData.responseText);
    errors = responseText.errors;
    non_field_errors = responseText.non_field_errors;
    $.each(errors, function(key, value) {
      //TODO: maybe need to like specify that we're looking for the
      //id thing within the given form.
      form.find('#id_'+key).closest('tr').append("<td class='form_error'>"+
        value+"</td>");
      return null;
    });
    var icon_URL = 'icons/delete.svg';
    var icon_description = 'error';
    report_form_finish(form, icon_URL, icon_description, non_field_errors);
    return null;
  };
  return report_errors;
};

var submit_function_creator = function(post_URL, choice_id) {
  var submit_function = function(e) {
    //Override the form's normal POST action.
    e.preventDefault();
    var data = {};
    var form = $(this);
    form.unbind()
      .find('.submit_button').prop('disabled', true);
    //TODO: again, this is probably inefficient. Just getting it working for now.
    form.find('.form_status').empty();
    form.find('.form_error').remove();
    $.each(form.serializeArray(), function(key, form_element) {
      data[form_element.name] = form_element.value;
    });
    //Not just testing `choice_id` because sometimes it is '' (although then
    //we don't expect to have a submit function.
    //TODO: maybe could just do this without checking. It's never used in situations
    //where it isn't defined.
    if (choice_id !== undefined) {
      data['choice_id'] = choice_id;
    }
    $.ajax({
      type: 'POST',
      url: post_URL,
      data: data,
      success: report_success_creator(form),
      error: report_errors_creator(form),
    });
    return null;
    };
  return submit_function;
};

var configure_create_form = function(index, args) {
  /*
  `index` is not used. `args` should be an array with entries
    0: Name of the object to be created (to identify the form).
    1: Name of the Django application in which the object is defined.
    2: Name of the object to be created (to determine which Django view function
       handles the request).
  */
  var create_URL = '/'+args[1]+'/actions/create/'+args[2]+'/';
  $('#'+args[0]+'_create_form').submit(submit_function_creator(create_URL));
};

var configure_edit_form = function(index, args) {
  /*
  `index` is not used. `args` should be an array with entries
    0: Name of the object to be edited (to identify the form).
    1: Name of the Django application in which the object is defined.
    2: Name of the object to be edited (to determine which Django view function
       handles the request).
  */
  var edit_URL = '/'+args[1]+'/actions/edit/'+args[2]+'/';
  $('#'+args[0]+'_edit_form_selector').find('select').change(function() {
    var main_form = $('#'+args[0]+'_edit_form');
    //Get rid of the submit function. It's going to be added again later, so this
    //prevents it from being called multiple times then. Could probably be made smoother.
    main_form.unbind()
    .empty();
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
};
