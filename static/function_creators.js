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
    if (errors) {
      alert('errors: '+String(errors.toSource()));
    }
    if (non_field_errors) {
      alert('non_field_errors: '+String(errors.toSource()));
    }
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
    form.find('.submit_button').prop('disabled', true);
    //TODO: again, this is probably inefficient. Just getting it working for now.
    form.find('.form_status').empty();
    form.find('.form_error').remove()
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
