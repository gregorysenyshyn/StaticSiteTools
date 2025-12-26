// Original Callback Form Logic (kept for backward compatibility if needed, but updated visually via CSS)
function submitRecaptchaForm(e, keyId, action, formName, successRedirect, errorRedirect) {
  e.preventDefault();
  const form = document.getElementById(formName);

  if (!form.reportValidity()) {
    return false;
  }

  const submitButtons = form.querySelectorAll('input[type="submit"], button[type="submit"]');
  for (let button = 0; button<submitButtons.length;button++){
    submitButtons[button].disabled = true;
    // Brutalist update: Change text instead of showing spinner
    if (submitButtons[button].tagName === 'INPUT') {
      submitButtons[button].value = "SENDING...";
    } else {
      submitButtons[button].textContent = "SENDING...";
    }
  }

  try {
    grecaptcha.enterprise.ready(async () => {
      try {
        const token = await grecaptcha.enterprise.execute(keyId, {action: action});
        const data = new FormData(form);
        data.append("token", token);
        data.append("action", action);
        const body = JSON.stringify(Object.fromEntries(data))
        const response = await fetch(form.action, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          mode: 'cors',
          body: body }
        )
        if (response["status"] === 200) {
          window.location.href = successRedirect;
        }
        else {
          window.location.href = errorRedirect;
        };
      } catch (error) {
        console.error('Form submission error:', error);
        window.location.href = errorRedirect;
      }
    })
  }
  catch (error) {
    console.error('Recaptcha error:', error);
    window.location.href = errorRedirect;
  }
}
