var functionCreators = function() {
  var Icon = function(symbol, cssClasses) {
    this.symbol = symbol;
    this.cssClasses = cssClasses;
    this.html = "<span class='"+this.cssClasses+"'>"+
      this.symbol+"</span>";
  };

  var reportSuccessCreator = function(form, postURL, choiceID) {
    return function(returnedData, textStatus, jqXHR) {
      return null;
    };
  };

  var reportErrorsCreator = function(form, postURL, choiceID) {
    return function(returnedData, textStatus, jqXHR) {
      var responseText = JSON.parse(returnedData.responseText);
      var errors = responseText.errors;
      var nonFieldErrors = responseText.non_field_errors;
      $.each(errors, function(key, value) {
        form.find('#id_'+key)
          .closest('tr')
          .append("<td class='form_error'>"+value+"</td>");
        return null;
      });
      form.find('.form_report')
        .append(nonFieldErrors.join(' '));
      return null;
    };
  };

  var public_methods = {};

  public_methods.submitFunctionCreator = function myself(
      postURL,
      choiceID,
      additionalSuccessFunctions
  ) {
    if (additionalSuccessFunctions === undefined) {
      additionalSuccessFunctions = [];
    }
    return function(e) {
      var form = $(this);
      var wrapAJAXFunction = function(ajaxFunction, icon) {
        var inner = function(returnedData, textStatus, jqXHR) {
          form.find('.form_status')
            .empty()
            .append(icon.html);
          ajaxFunction(returnedData, textStatus, jqXHR);
          form.submit(myself(postURL, choiceID, additionalSuccessFunctions))
            .find('.submit_button')
            .prop('disabled', false);
          return null;
        };
        return inner;
      };
      //Override the form's normal POST action.
      e.preventDefault();
      form.unbind()
        .find('.submit_button').prop('disabled', true);
      //TODO: again, this is probably inefficient. Just getting it working for now.
      form.find('.form_status').empty();
      form.find('.form_report').empty();
      form.find('.form_error').remove();
      var data = {};
      $.each(form.serializeArray(), function(key, formElement) {
        data[formElement.name] = formElement.value;
      });
      data.choice_id = choiceID;
      var successFunctions = [
        wrapAJAXFunction(
          reportSuccessCreator(form),
          new Icon('✔ Accepted.', 'form_success')
        ),
      ];
      successFunctions = successFunctions.concat(additionalSuccessFunctions);
      $.ajax({
        type: 'POST',
        url: postURL,
        data: data,
        beforeSend: function(jqXHR, settings) {
          if (!this.crossDomain) {
            jqXHR.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
          }
          return null;
        },
        //TODO: try using a `complete` function, maybe. It would still depend on the
        //icon, though. Separate the icon stuff and the recursive call of `myself`?
        success: successFunctions,
        error: wrapAJAXFunction(
          reportErrorsCreator(form),
          new Icon('✖ Rejected.', 'form_error')
        ),
      });
      return null;
    };
  };

  public_methods.configureCreateForm = function(_, formSubmitter) {
    var createURL = '/'+formSubmitter.objectGrouping+ '/actions/create/'+
      formSubmitter.objectName+'/';
    $('#'+formSubmitter.htmlName+'_create_form').submit(
      public_methods.submitFunctionCreator(createURL, undefined));
      return null;
  };

  public_methods.configureEditForm = function(_, formSubmitter) {
    var editURL = '/'+formSubmitter.objectGrouping+'/actions/edit/'+
      formSubmitter.objectName+'/';
    $('#'+formSubmitter.htmlName+'_edit_form_selector').find('select')
      .change(function() {
        var mainForm = $('#'+formSubmitter.htmlName+'_edit_form');
        //Get rid of the submit function. It's going to be added again later,
        //so this prevents it from being called multiple times then. Could
        //probably be made smoother.
        mainForm.unbind()
          .empty();
        var choiceID = $(this).val();
        if (choiceID) {
          var loadingMessageID = 'selector_loading_message';
          //TODO: add a class for the loading message. Failure message could
          //go there, too.
          $(this).closest('tr')
            .append("<td id='"+loadingMessageID+"'>Loading ...</td>");
          $.get(
            editURL,
            {choice_id: choiceID},
            function (returnedData, textStatus, jqXHR) {
              //TODO: instead maybe we could first check whether the td is
              //present, and so on.
              $('#'+loadingMessageID).remove();
              mainForm.append(returnedData)
                .submit(
                  public_methods.submitFunctionCreator(editURL, choiceID)
                );
              //Enable any datepickers that have just been added.
              //TODO: any less crude way to do this?
              $('.date_picker').datepicker({dateFormat: 'yy-mm-dd'});
            });
        }
        return null;
      });
    return null;
  };

  public_methods.FormSubmitter = function(htmlName, objectGrouping, objectName) {
    //TODO: adapt this to however you decide to document JavaScript functions.
    //0: Name of the object to be created (to identify the form).
    //1: Name of the Django application in which the object is defined.
    //2: Name of the object to be created (to determine which Django view function
    //handles the request).
    this.htmlName = htmlName;
    this.objectGrouping = objectGrouping;
    this.objectName = objectName;
  };

  return public_methods;
}();
