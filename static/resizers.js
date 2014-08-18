$(document).ready(function() {
  $main_content = $('#main_content');
  var paddings = 0;
  $.each(['top', 'bottom'], function(index, element) {
    paddings += parseFloat($main_content.css('padding-'+element));
  });
  var min_height = $(window).height()-($('#header').height()+$('#footer').height()+paddings);
  if ($main_content.height() < min_height) {
    $main_content.height(min_height);
  }
});
