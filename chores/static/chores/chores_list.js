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

var fetchInterval = 60;
var lastFetchMilliseconds = (new Date()).getTime();
//TODO: to use if you get setTimeout working.
//var changes_made = false;

var insertChores = function(data, textStatus, jqXHR) {
  var responseAsObject = JSON.parse(data);
  $('#chores').prepend(responseAsObject.html);
  cycleOffsetToFetch -= 1;
  if (firstLoad) {
    try {
      console.log('trying to scroll to today');
      $('html,body').animate({scrollTop: $('a[name=today]').offset().top}, 1000);
      console.log('apparently, successfully scrolled to today');
    } catch (e) {
      console.log(e);
      //There is probably no element named 'today'. Scroll to the top instead.
      window.scrollTo(0, 0);
    }
    firstLoad = false;
  } else {
    //TODO: remove, as Valentine requested.
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
  var responseAsObject = JSON.parse(data);
  $.each(responseAsObject.chores, function(chore_id, chore_HTML) {
    $('#chore_button_'+chore_id).prop('disabled', !chore_HTML.button.enabled)
      .removeClass()
      .addClass('chore_button styled_button '+chore_HTML.CSS_classes);
    $('#chore_button_text_'+chore_id).empty().append(chore_HTML.button.text);
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

var displayChoreForm = function(chore_id) {
  var inner = function(data, textStatus, jqXHR) {
	//$('#chore_form_dialog").empty()
		//.append('<form id="chore_edit_form">')
		//.append(data)
		//.append('</form>')
		//.find('form')
  $('#chore_edit_form').empty()
    .append(data)
		.submit(functionCreators.submitFunctionCreator(
      '/chores/actions/edit/chore/', chore_id))
		.dialog({
      close: function(event, ui) {
        $('#steward_button_'+chore_id).prop('disabled', false);
				fetchUpdates();
      },
			modal: true,
			width: 'auto',
		})
  };
  return loaderClear(inner);
};

var AJAXCreator = function(method_name) {
  var inner = function(chore_id) {
    $('#chore_button_'+chore_id).prop('disabled', true);
    $.ajax({
      url: '/chores/actions/',
      //Calling it `choice_id` to match up with the general functions for
      //fetching objects.
      data: {'method_name': method_name, 'choice_id': chore_id},
      type: 'POST',
      async: true,
      success: replaceSentences,
      error: function(jqXHR, textStatus, errorThrown) {
        alert('Error: '+jqXHR.statusText+' '+jqXHR.responseText);
      },
      complete: function() {},
      beforeSend: csrfBeforeSend,
    });
  };
  return loaderMessage(inner, 'saving');
};

var clickChore = AJAXCreator('deduce');

var fetchChoreForm = function(chore_id) {
	$('#steward_button_'+chore_id).prop('disabled', true);
	$.ajax({
		url: '/chores/actions/edit/chore/',
		data: {'choice_id': chore_id},
		type: 'GET',
		async: true,
		success: displayChoreForm(chore_id),
		error: function(jqXHR, textStatus, errorThrown) {
			alert('Error: '+jqXHR.statusText+' '+jqXHR.responseText);
		},
		complete: function() {},
		beforeSend: csrfBeforeSend,
	});
};
fetchChoreForm = loaderMessage(fetchChoreForm, 'fetching');

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
  fetchChores();
  fetchUpdates();
  //See note above.
  fetchUpdates = loaderMessage(fetchUpdates, 'updating');
  setInterval(fetchUpdates, 1000*fetchInterval);
  $(this).scroll(function() {
    if (this.pageYOffset == 0) {
      console.log('going to call fetchChores');
      fetchChores();
      console.log('called fetchChores');
    }
  });
});
