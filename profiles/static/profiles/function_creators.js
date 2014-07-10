var report_form_icon = function(form, icon_URL, icon_description) {
  //TODO: 'static' here is replacing '{% static %} in the Django template'.
  var form_icon = form.find('.form_icon');
  form_icon.empty();
  form_icon.append('<object data="/static/'+icon_URL+'">'+icon_description+
      '</object>');
  return null;
};

var report_success_creator = function(form) {
  var report_success = function(returnedData, textStatus, jqXHR) {
    var icon_URL = 'icons/checkmark.svg';
    var icon_description = 'checkmark';
    var form_icon = form.find('.form_icon');
    report_form_icon(form, icon_URL, icon_description);
    return null;
  };
  return report_success;
};

var report_errors_creator = function(form) {
  var report_errors = function(returnedData, textStatus, jqXHR) {
    returnedData = JSON.parse(returnedData);
    alert('in report_errors');
    alert(JSON.stringify(returnedData));
    alert('did JSON parse');
    //var errors = returnedData.errors;
    //var non_field_errors = returnedData.non_field_errors;
    alert('right before first forEach');
    returnedData.errors.forEach(function(key) {
      $('#id_'+key).closest('tr').append("<td class='form_error'>"+ errors[key]+
        "</td>");
    });
    alert('right before second forEach');
    returnedData.non_field_errors.forEach(function(key) {
      //TODO: put these somewhere.
    });
    alert('right after all forEaches');
    var icon_URL = 'icons/delete.svg';
    var icon_description = 'error';
    report_form_icon(form, icon_URL, icon_description);
    report('about to leave report_errors');
    return null;
  };
  return report_errors;
};

//TODO: can test whether binding `this` to the argument `that` is needed. Tend
//to think that this is unneeded, but haven't tested and it depends on how the
//jQuery `submit` method works.
var submit_function_creator = function(post_URL) {
  //TODO: disable the submit button!
  var submit_function = function(e) {
    //Override the form's normal POST action.
    e.preventDefault();
    var data = {};
    var form = $(this);
    form.serializeArray().forEach(function(form_element) {
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
