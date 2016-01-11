var columnize = function($element) {
  var spacer_width = 1*parseFloat($element.css('font-size'), 10);
  var main_content_width = $('#main_content').width();
  var cell_width = $element.find('tr').width();
  var num_columns = Math.floor(main_content_width/(cell_width+spacer_width));
  spacer_width = String(spacer_width);
  if (num_columns == 1) {
    return;
  }
  var entry_htmls = [];
  $.each($element.find('tr'), function(index, row) {
    $row = $(row);
    entry_htmls.push($row.html());
    $row.remove();
  });
  var column;
  var table_html = '';
  $.each(entry_htmls, function(index, entry_html) {
    column = index % num_columns;
    if (column === 0) {
      entry_html = '<tr>'+entry_html;
    }
    if (column == num_columns-1) {
      entry_html = entry_html+'</tr>';
    } else {
      entry_html = entry_html+'<td style="width: '+spacer_width+'"></td>';
    }
    table_html += entry_html;
  });
  if (column != num_columns-1) {
    table_html += '</tr>';
  }
  $element.append(table_html);
};

var resizeMainContent = function() {
  var threshold_width = 680;
  $main_content = $('#main_content');
	var paddings = $main_content.outerHeight()-$main_content.height();
  var headerHeight = 0;
  var sidebarWidth = 0;
  $leftSidebar = $('#left_sidebar');
  if ($(window).width() <= threshold_width) {
    headerHeight = $leftSidebar.outerHeight();
  } else {
    sidebarWidth = $leftSidebar.outerWidth();
  }
  paddings -= headerHeight;
	var min_height = $(window).height()-paddings;
  if ($main_content.height() < min_height) {
    $main_content.css('min-height', min_height);
  }
  $main_content.css('margin-top', headerHeight);
  $main_content.css('margin-left', sidebarWidth);
};

var repositionNavBar = function() {
  $nav_bar = $('#nav_bar');
  if ($nav_bar.width() + $('#logo').width() < $(window).width()) {
    $nav_bar.css('margin-top', ($('#header').height()-$nav_bar.height())/2);
  }
};

$(window).load(function() {
  resizeMainContent();
  repositionNavBar();
});
