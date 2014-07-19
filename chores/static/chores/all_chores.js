var replaceSentencesCreator = function(chore_id) {
  var replaceSentences = function(data, textStatus, jqXHR) {
    var responseAsObject = JSON.parse(data);
    responseAsObject.sentences.forEach(function(sentence) {
      var sentenceElement = $('#'+sentence.identifier+'_sentence_'+chore_id);
      sentenceElement.empty();
      if (sentence.report) {
        sentenceElement.append(sentence.report_text);
      }
      if (sentence.button) {
        sentenceElement.append('<button class="'+sentence.identifier+'_button"'+
          'id="'+sentence.identifier+'_button_'+chore_id+'"'+
          'onclick="'+sentence.JavaScript_function+'('+chore_id+')">'+
          sentence.button_text+'</button>');
      }
      return null;
    });
    var choreElement = $('#chore_'+chore_id);
    choreElement.removeClass();
    choreElement.addClass(responseAsObject.CSS_classes);

    var currentBalance = $('#current_balance');
    currentBalance.empty();
    currentBalance.append(responseAsObject.current_balance.value);
    currentBalance.removeClass();
    currentBalance.addClass(responseAsObject.current_balance.CSS_class);
    return null;
  };
  return replaceSentences;
};

var AJAXCreator = function(URL_function, signature_name) {
  var inner = function(chore_id) {
    $('#'+signature_name+'_button_'+chore_id).prop('disabled', true);
    $.ajax({
      //TODO: send in `chore_id` as data, not as part of the URL.
      url: '/chores/actions/'+URL_function+'/'+chore_id+'/',
      type: 'POST',
      async: true,
      success: replaceSentencesCreator(chore_id),
      error: function(jqXHR, textStatus, errorThrown) {
	alert('Error: '+jqXHR.statusText+jqXHR.responseText);
      },
      complete: function() {}
    });
  };
  return inner;
};

var signUpChore        = AJAXCreator('sign_up', 'signed_up');
var signOffChore       = AJAXCreator('sign_off', 'signed_off');
var voidChore          = AJAXCreator('void', 'voided');
var revertSignUpChore  = AJAXCreator('revert_sign_up', 'signed_up');
var revertSignOffChore = AJAXCreator('revert_sign_off', 'signed_off');
var revertVoidChore    = AJAXCreator('revert_void', 'voided');
