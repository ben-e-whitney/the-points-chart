//TODO: here and elsewhere, follow JavaScript convention for variable names.
var csrf_token = $.cookie('csrftoken');
var CSRF_before_send = function(jqXHR, settings) {
  if (!this.crossDomain) {
    jqXHR.setRequestHeader('X-CSRFToken', csrf_token);
  }
};

var fetch_interval = 10*60;
var last_fetch_milliseconds = (new Date()).getTime();
//TODO: to use if you get setTimeout working.
//var changes_made = false;

var replaceSentences = function(data, textStatus, jqXHR) {
  var prepend_sign = function(balance) {
    var sign;
    if (balance >= 0) {
      sign = '+';
    } else {
      sign = '−';
    }
    return sign+String(Math.abs(balance));
  };
  var make_new_button = function(sentence, chore_id) {
    var CSS_classes = sentence.identifier+'_button';
    if (sentence.JavaScript_function && sentence.JavaScript_function.indexOf('revert') != -1) {
      CSS_classes += ' revert';
    }
    if (!sentence.button) {
      CSS_classes += ' no_button';
    }
    CSS_classes = '"'+CSS_classes+'"';
    var enabled = '';
    if (!sentence.button) {
      enabled = ' disabled=""';
    }
    var button_id = '"'+sentence.identifier+'_button_'+chore_id+'"';
    var button_onclick = '"'+sentence.JavaScript_function+'('+chore_id+')"';
    var html = '<button class='+CSS_classes+' id='+button_id+
      ' onclick='+button_onclick+enabled+'> '+sentence.button_text+'</button>';
    return html;
  };
  var responseAsObject = JSON.parse(data);
  $.each(responseAsObject.chores, function(chore_id, chore_HTML) {
    $.each(chore_HTML.sentences, function(index, sentence) {
      var $sentenceElement = $('#'+sentence.identifier+'_sentence_'+chore_id);
      $sentenceElement.empty();
      if (sentence.report) {
        $sentenceElement.append(sentence.report_text);
      }
      $('#'+sentence.identifier+'_button_'+chore_id).replaceWith(
        make_new_button(sentence, chore_id));
      return null;
    });
    $('#chore_'+chore_id).removeClass()
      .addClass(chore_HTML.CSS_classes);
    return null;
  });
  var $current_balance = $('#current_balance');
  if (responseAsObject.hasOwnProperty('current_balance')) {
    $current_balance.empty()
      .append(prepend_sign(responseAsObject.current_balance.value))
      .removeClass()
      .addClass(responseAsObject.current_balance.CSS_class);
   }
  if (responseAsObject.hasOwnProperty('balance_change')) {
    var balance = parseFloat($current_balance.html().replace('−', '-'), 10);
    $current_balance.html(prepend_sign(balance+responseAsObject.balance_change));
  }
  $current_balance.fadeIn();
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
	$('table.chores_list').each(function(index, element) {columnize($(element));});

  $('html,body').animate({scrollTop: $('a[name=today]').offset().top}, 1500)
  fetch_updates();
  setInterval(fetch_updates, 1000*fetch_interval);
  $('#current_balance').hover(
    function(eventObject) {$(this).stop().fadeTo('slow', 0);},
    function(eventObject) {$(this).stop().fadeTo('slow', 1);}
  );
});
