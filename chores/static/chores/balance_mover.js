var get_distance = function($that, $window, location, dimension_method, css_attributes) {
  var one_quadratic_root = function(a, b, c, root) {
    c /= a;
    b /= a;
    a = 1;
    //Because `a` is `1`, adding the sqrt root of the discriminant will make for a larger root.
    return (-b+(root == 'larger' ? 1 : -1)*Math.pow(Math.pow(b, 2)-4*a*c, 1/2))/(2*a);
  };
  //`S` is the width (resp. height) of `$that` ('self') and `W` is the width (resp. height)
  //of the window. We'll generate the next location according to a probability distribution
  //that (unweighted) is 1 at 0, 0 at `S`, and 1 at `W-S`. This should serve to propel the 
  //element away from its current location.
  var S = $that[dimension_method]();
  var W = $window[dimension_method]();
  $.each(css_attributes, function(index, attribute) {
    S += parseFloat($that.css(attribute));
  });
  var inverse = function(p) {
    if (p < S/(W-S)) {
      return one_quadratic_root(1/(S*(S-W)), 2/(W-S), -p, 'smaller');
    } else {
      return one_quadratic_root(1, -2*S, Math.pow(S, 2)-(W-S)*(W-2*S)*(p-S/(W-S)), 'larger');
    }
  };
  return String(inverse(Math.random())-location)+'px';
};
var counter = 0;
var jump_around = function(event) {
  var $this = $(this);
  var $window = $(window);
  //Disable the function until this action completes.
  $this.off('mouseenter', jump_around);
  var offset = $this.offset();
  var left_distance = get_distance($this, $window, offset.left,
                                   'width',  ['padding-left', 'padding-right']);
  var top_distance  = get_distance($this, $window, offset.top-$window.scrollTop(),
                                   'height', ['padding-top',  'padding-bottom']);
  if (counter < 50) {
    $this.animate({
      'left'  : '+='+left_distance,
      'right' : '-='+left_distance,
      'top'   : '+='+top_distance,
      'bottom': '-='+top_distance,
    });
    counter += 1;
  } else {
    $this.text('☺');
  }
  //Reenable the function.
  $this.on('mouseenter', jump_around);
  return null;
};

$(document).ready(function() {
  //TODO: there is some bug here that occasionally (on the order of 1/50 movements) causes
  //the element to leave the window. It's funny when it happens so this has low priority.
  $('#current_balance').mouseenter(jump_around);
});
