var report_errors_creator = function(form) {
  var report_errors = function(returnedData) {
    //TODO: Clear old errors. Get this to just be for errors in the current form
    //alert('about to clear');
    form.find('.form_error').empty();
    returnedData = JSON.parse(returnedData);
    var errors = returnedData.errors;
    var non_field_errors = returnedData.non_field_errors;
    var form_acceptable = true;
    for (key in errors) {
      $('#id_'+key).closest('tr').append("<td class='form_error'>"+ errors[key]+
        "</td>");
    }
    non_field_errors.forEach(function(key) {
      //TODO: put these somewhere.
    });
    form_icon = form.find('.form_icon');
    form_icon.empty()
    //TODO: 'static' here is replacing '{% static %} in the Django template'.
    if ($.isEmptyObject(errors) && $.isEmptyObject(non_field_errors)) {
      var icon_URL = 'icons/white/checkmark_green.svg';
      var icon_description = 'checkmark';
    } else {
      var icon_URL = 'icons/white/delete_red.svg';
      var icon_description = 'error';
    }
    form_icon.append('<object data="/static/'+icon_URL+'">'+icon_description+
        '</object>');
  };
  return report_errors;
};

$(document).ready(function() {
  $('#profile_form').submit(function(e) {
    //Override the form's normal POST action.
    e.preventDefault();
    var data = {};
    var form = $(this);
    form.serializeArray().forEach(function(form_element) {
      data[form_element.name] = form_element.value;
    });
    $.post('actions/edit/', data, report_errors_creator(form));
    return null;
  });
});
