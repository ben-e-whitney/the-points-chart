//TODO: here and elsewhere, follow JavaScript convention for variable names.
var csrf_token = $.cookie('csrftoken');
var CSRF_before_send = function(jqXHR, settings) {
  if (!this.crossDomain) {
    jqXHR.setRequestHeader('X-CSRFToken', csrf_token);
  }
};

var fetch_interval = 30;
var last_fetch_milliseconds = (new Date()).getTime();
//TODO: to use if you get setTimeout working.
//var changes_made = false;

var replaceSentences = function(data, textStatus, jqXHR) {
  var responseAsObject = JSON.parse(data);
  //changes_made = $.isEmptyObject(responseAsObject.chores);
  $.each(responseAsObject.chores, function(chore_id, chore_HTML) {
    $.each(chore_HTML.sentences, function(index, sentence) {
      var $sentenceElement = $('#'+sentence.identifier+'_sentence_'+chore_id);
      $sentenceElement.empty();
      if (sentence.report) {
        $sentenceElement.append(sentence.report_text);
      }
      if (sentence.button) {
        $sentenceElement.append('<button class="'+sentence.identifier+'_button"'+
          ' id="'+sentence.identifier+'_button_'+chore_id+'"'+
          ' onclick="'+sentence.JavaScript_function+'('+chore_id+')">'+
          sentence.button_text+'</button>');
      }
      return null;
    });
    $('#chore_'+chore_id).removeClass()
      .addClass(chore_HTML.CSS_classes);
    return null;
  });
  $('#current_balance').empty()
    .append(responseAsObject.current_balance.value)
    .removeClass()
    .addClass(responseAsObject.current_balance.CSS_class);
  return null;
};

var AJAXCreator = function(URL_function, signature_name) {
  var inner = function(chore_id) {
    //TODO: there is something funny going on here. Some buttons get voided right
    //at the beginning.
    $.each(['signed_up', 'signed_off', 'voided'], function(index, signature_name) {
      $('#'+signature_name+'_button_'+chore_id).prop('disabled', true);
    });
    $.ajax({
      //TODO: send in `chore_id` as data, not as part of the URL.
      url: '/chores/actions/'+URL_function+'/',
      data: {'chore_id': chore_id},
      type: 'POST',
      async: true,
      success: replaceSentences,
      error: function(jqXHR, textStatus, errorThrown) {
	alert('Error: '+jqXHR.statusText+jqXHR.responseText);
      },
      complete: function() {},
      beforeSend: CSRF_before_send,
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

var fetch_updates = function() {
  var new_milliseconds = (new Date()).getTime();
  $.get('/chores/actions/fetch/updates/',
        {'milliseconds': last_fetch_milliseconds},
        replaceSentences
  );
  last_fetch_milliseconds = new_milliseconds;
};

$(window).load(function() {
  $('html,body').animate({scrollTop: $('a[name=today]').offset().top}, 0)
  setInterval(fetch_updates, 1000*fetch_interval);
});
