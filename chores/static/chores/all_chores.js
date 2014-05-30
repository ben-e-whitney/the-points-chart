var signUp = function(instance_id) {
  //Using a closure for something. Forget what.
  var xhr = new XMLHttpRequest();
  //Could add some error catching here in the case of very old browsers.
  xhr.onreadystatechange = function() {
    if (this.readyState == 4) {
      if (this.status == 200) {
        var responseAsObject = JSON.parse(this.response);
        var elementIdPrefixes = ["sign_up_sentence", "sign_off_sentence"];
        elementIdPrefixes.forEach(function(key) {
          document.getElementById(key+"_"+instance_id).innerHTML =
            responseAsObject[key];
          return null;
        })
        //TODO: use classList.toggle here instead?
        document.getElementById("instance_"+instance_id).classList.remove(
            "needs_sign_up")
        document.getElementById("instance_"+instance_id).classList.add(
            "user_signed_up")
        document.getElementById("instance_"+instance_id).classList.add(
            "needs_sign_off")
      } else if (this.status == 403) {
        alert('Error: '+this.statusText+this.responseText);
      }
    }
  };
  xhr.open('POST', '/chores/sign_up/'+instance_id+'/', true);
  xhr.send(null);
}

var signOff = function(instance_id) {
  var xhr = new XMLHttpRequest();
  //Could add some error catching here in the case of very old browsers.
  xhr.onreadystatechange = function() {
    if (this.readyState == 4) {
      if (this.status == 200) {
        var responseAsObject = JSON.parse(this.response);
        var elementIdPrefixes = ["sign_off_sentence"];
        elementIdPrefixes.forEach(function(key) {
          document.getElementById(key+"_"+instance_id).innerHTML =
            responseAsObject[key];
          return null;
        })
        document.getElementById("instance_"+instance_id).classList.remove(
            "needs_sign_off")
        document.getElementById("instance_"+instance_id).classList.add(
            "user_signed_off")
      } else if (this.status == 403) {
        alert('Error: '+this.statusText+this.responseText);
      }
    }
  };
  xhr.open('POST', '/chores/sign_off/'+instance_id+'/', true);
  xhr.send(null);
}
