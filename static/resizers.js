var columnize = function($element) {
  var spacer_width = 1*parseFloat($element.css('font-size'), 10);
  var main_content_width = $('#main_content').width();
  var cell_width = $element.find('tr').width();
  var num_columns = Math.floor(main_content_width/(cell_width+spacer_width));
  spacer_width = String(spacer_width);
  if (num_columns == 1) {
    return;
  }
  var entry_htmls = []
  $.each($element.find('tr'), function(index, row) {
    $row = $(row);
    entry_htmls.push($row.html());
    $row.remove();
  });
  var column;
  var table_html = ''
  $.each(entry_htmls, function(index, entry_html) {
    column = index % num_columns;
    if (column == 0) {
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

$(window).load(function() {
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
