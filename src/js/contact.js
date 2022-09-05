var contactFormPostAddress = 'https://9ggyqojqkg.execute-api.us-east-1.amazonaws.com/normal'
var formId = 'contact-form';

function submitForm (data, address) {
  var xhr  = new XMLHttpRequest();
  xhr.addEventListener('load', function(event) {
      console.log(xhr.responseText);
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

function getFormData() {
  var data = {};
  data.recaptchaKey = grecaptcha.getResponse();
  data.name = document.getElementById("contact-name-input").value;
  data.phone = document.getElementById("contact-phone-input").value;
  data.email = document.getElementById("contact-email-input").value;
  data.message = document.getElementById("contact-message-input").value;
  return data;
}

function submitContactForm() {
  var data = getFormData();
  var response = submitForm(data, contactFormPostAddress);
  document.getElementById(formId).reset();
}
