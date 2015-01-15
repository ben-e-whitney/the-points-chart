var firstLoad = true;
var cycleOffsetToFetch = 0;

//This value is in pixels and I am not confident it will always work.
var resizeCurrentBalance = function(currentBalance) {
  var defaultFontSize = 48;
  var defaultLength = 3;
  if (currentBalance.length <= defaultLength) {
    return defaultFontSize;
  } else {
    return defaultFontSize*defaultLength/currentBalance.length;
  }
};

var loaderMessage = function(func, message) {
  var wrappedFunction = function() {
    var $loaderImage = $('#loaderImage');
    $loaderImage.show();
    var $loaderMessage = $('#loaderMessage');
    $loaderMessage.html(message+' &hellip;')
      .css('right', 1.1*$loaderImage.width())
      .css('top', 0.5*($loaderImage.height()-$loaderMessage.height()));
    func.apply(this, arguments);
  };
  return wrappedFunction;
};

var loaderClear = function(func) {
  var wrappedFunction = function() {
    func.apply(this, arguments);
    $('#loaderImage').hide();
    $('#loaderMessage').fadeOut()
      .empty()
      .fadeIn();
  };
  return wrappedFunction;
};

//TODO: here and elsewhere, follow JavaScript convention for variable names.
var csrfToken = $.cookie('csrftoken');
var csrfBeforeSend = function(jqXHR, settings) {
  if (!this.crossDomain) {
    jqXHR.setRequestHeader('X-CSRFToken', csrfToken);
  }
};

var fetchInterval = 10*60;
var lastFetchMilliseconds = (new Date()).getTime();
//TODO: to use if you get setTimeout working.
//var changes_made = false;

var insertChores = function(data, textStatus, jqXHR) {
  var responseAsObject = JSON.parse(data);
  //TODO: disable button if the first cycle is already loaded.
  if (responseAsObject.least_cycle_num == 1) {
    $('#load_more_button').prop('disabled', true);
  }
  $('#chores').prepend(responseAsObject.html);
  cycleOffsetToFetch -= 1;
  if (firstLoad) {
    $('html,body').animate({scrollTop: $('a[name=today]').offset().top}, 1000);
    firstLoad = false;
  } else {
    window.scrollTo(0, 0);
  }
  return null;
};
insertChores = loaderClear(insertChores);

var replaceSentences = function(data, textStatus, jqXHR) {
  var prependSign = function(balance) {
    var sign;
    if (balance >= 0) {
      sign = '+';
    } else {
      sign = '−';
    }
    return sign+String(Math.abs(balance));
  };
  var makeNewButton = function(sentence, chore_id) {
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
        makeNewButton(sentence, chore_id));
      return null;
    });
    $('#chore_'+chore_id).removeClass()
      .addClass('chore_cell')
      .addClass(chore_HTML.CSS_classes);
    return null;
  });
  var $current_balance = $('#current_balance');
  var fontSize;
  if (responseAsObject.hasOwnProperty('current_balance')) {
    fontSize = resizeCurrentBalance(responseAsObject.current_balance.formatted_value);
    $current_balance.empty()
      .css('font-size', fontSize)
      .append(responseAsObject.current_balance.formatted_value)
      .removeClass()
      .addClass(responseAsObject.current_balance.CSS_class);
   }
  if (responseAsObject.hasOwnProperty('balance_change')) {
    var balance = parseFloat($current_balance.html().replace('−', '-'), 10);
    balance = prependSign(balance+responseAsObject.balance_change);
    fontSize = resizeCurrentBalance(balance);
    $current_balance.css('font-size', fontSize)
      .html(balance);
  }
  return null;
};
replaceSentences = loaderClear(replaceSentences);

var AJAXCreator = function(urlFunction, signatureName) {
  var inner = function(chore_id) {
    //TODO: there is something funny going on here. Some buttons get voided right
    //at the beginning.
    $.each(['signed_up', 'signed_off', 'voided'], function(index, signatureName) {
      $('#'+signatureName+'_button_'+chore_id).prop('disabled', true);
    });
    $.ajax({
      //TODO: send in `chore_id` as data, not as part of the URL.
      url: '/chores/actions/'+urlFunction+'/',
      data: {'chore_id': chore_id},
      type: 'POST',
      async: true,
      success: replaceSentences,
      error: function(jqXHR, textStatus, errorThrown) {
  alert('Error: '+jqXHR.statusText+jqXHR.responseText);
      },
      complete: function() {},
      //TODO: does this need to be used for other AJAX requests as well?
      beforeSend: csrfBeforeSend,
    });
  };
  return loaderMessage(inner, 'saving');
};

var signUpChore        = AJAXCreator('sign_up', 'signed_up');
var signOffChore       = AJAXCreator('sign_off', 'signed_off');
var voidChore          = AJAXCreator('void', 'voided');
var revertSignUpChore  = AJAXCreator('revert_sign_up', 'signed_up');
var revertSignOffChore = AJAXCreator('revert_sign_off', 'signed_off');
var revertVoidChore    = AJAXCreator('revert_void', 'voided');

var fetchUpdates = function() {
  var newMilliseconds = (new Date()).getTime();
  $.get('/chores/actions/fetch/updates/',
        {'milliseconds': lastFetchMilliseconds},
        replaceSentences
  );
  lastFetchMilliseconds = newMilliseconds;
};
//Delaying this (temporarily, maybe) until after it's called once so that the
//message from fetching chores isn't immediately overridden when the page is
//loaded.
//fetchUpdates = loaderMessage(fetchUpdates, 'updating');

var fetchChores = function() {
  $.get('/chores/actions/fetch/chores/',
        {'cycle_offset': cycleOffsetToFetch},
        insertChores
  );
  return null;
};
fetchChores = loaderMessage(fetchChores, 'loading');

$(window).load(function() {
  fetchChores(0);
  fetchUpdates();
  //See note above.
  fetchUpdates = loaderMessage(fetchUpdates, 'updating');
  setInterval(fetchUpdates, 1000*fetchInterval);
});
