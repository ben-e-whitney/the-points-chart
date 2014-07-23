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
    errors           = responseText.errors;
    non_field_errors = responseText.non_field_errors;
    $.each(errors, function(key, value) {
      $('#id_'+key).closest('tr').append("<td class='form_error'>"+
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

var submit_function_creator = function(post_URL) {
  var submit_function = function(e) {
    //Override the form's normal POST action.
    e.preventDefault();
    var data = {};
    var form = $(this);
    form.find('.submit_button').prop('disabled', true);
    $.each(form.serializeArray(), function(key, form_element) {
      data[form_element.name] = form_element.value;
    });
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
