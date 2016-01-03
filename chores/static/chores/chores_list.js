$(window).load(function() {
  fetchChores();
  fetchUpdates();
  //Delaying this redefinition until after it's called once so that the message
  //from fetching chores isn't immediately overridden when the page is loaded.
  fetchUpdates = loaderMessage(fetchUpdates, 'updating');
  setInterval(fetchUpdates, 1000*fetchInterval);
  $(this).scroll(function() {
    if (this.pageYOffset == 0) {
      fetchChores();
    }
  });
});
