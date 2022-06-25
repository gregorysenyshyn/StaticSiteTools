function submitForm (data, address) {
  let xhr  = new XMLHttpRequest();
  xhr.addEventListener('load', function(event) {
      console.log(xhr.responseText);
      // add redirect to thank-you page
      alert('Thanks for getting in touch!');
    }
  );
  xhr.addEventListener('error', function(event) {
      console.log(xhr.response);
      alert('There was an error sending your message.');
    }
  );
  xhr.open('POST', address);
  xhr.send(JSON.stringify(data));
}

function getFormData(recaptchaSitekey, submitAddress, fields) {
  grecaptcha.ready(function() {
    grecaptcha.execute(recaptchaSitekey, {action: 'submit'}).then(function(token) {
      let data = {'recaptchaToken': token};
      for (item in fields) {
        data[item] = document.getElementById(fields[item]).value;
      }
      submitForm(data, submitAddress)
    });
  });
}
