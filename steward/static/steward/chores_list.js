//This will prevent the page from scrolling onces the chores are inserted. 
firstLoad = false;
//Redefine `fetchChores`.
fetchChores = function() {
  $.get('/chores/actions/fetch/chores/',
				{'attention_needed': true},
        insertChores
  );
  return null;
};
fetchChores = loaderMessage(fetchChores, 'loading');

$(window).load(function() {
  fetchChores();
});
