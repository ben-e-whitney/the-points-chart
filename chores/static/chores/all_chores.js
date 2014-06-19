var signUp = function(chore_id) {
  //Using a closure for something. Forget what.
  var xhr = new XMLHttpRequest();
  //Could add some error catching here in the case of very old browsers.
  xhr.onreadystatechange = function() {
    if (this.readyState == 4) {
      if (this.status == 200) {
        var responseAsObject = JSON.parse(this.response);
        var elementIdPrefixes = ["sign_up_sentence", "sign_off_sentence"];
        elementIdPrefixes.forEach(function(key) {
          document.getElementById(key+"_"+chore_id).innerHTML =
            responseAsObject[key];
          return null;
        })
        //TODO: use classList.toggle here instead?
        document.getElementById("chore_"+chore_id).classList.remove(
            "needs_sign_up")
        document.getElementById("chore_"+chore_id).classList.add(
            "user_signed_up")
        document.getElementById("chore_"+chore_id).classList.add(
            "needs_sign_off")
      } else if (this.status == 403) {
        alert('Error: '+this.statusText+this.responseText);
      }
    }
  };
  xhr.open('POST', '/chores/sign_up/'+chore_id+'/', true);
  xhr.send(null);
}

var signOff = function(chore_id) {
  var xhr = new XMLHttpRequest();
  //Could add some error catching here in the case of very old browsers.
  xhr.onreadystatechange = function() {
    if (this.readyState == 4) {
      if (this.status == 200) {
        var responseAsObject = JSON.parse(this.response);
        var elementIdPrefixes = ["sign_off_sentence"];
        elementIdPrefixes.forEach(function(key) {
          document.getElementById(key+"_"+chore_id).innerHTML =
            responseAsObject[key];
          return null;
        })
        document.getElementById("chore_"+chore_id).classList.remove(
            "needs_sign_off")
        document.getElementById("chore_"+chore_id).classList.add(
            "user_signed_off")
      } else if (this.status == 403) {
        alert('Error: '+this.statusText+this.responseText);
      }
    }
  };
  xhr.open('POST', '/chores/sign_off/'+chore_id+'/', true);
  xhr.send(null);
}
