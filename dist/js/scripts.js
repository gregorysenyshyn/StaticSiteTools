(function() {
  // ⚡ Bolt: Cache header element to avoid repeated DOM queries
  const header = document.getElementById("header");
  let ticking = false;
  let lastOpacity = 1; // Track last applied opacity

  if (header) {
    window.addEventListener("scroll", function () {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

          // ⚡ Bolt: Clamp opacity and avoid unnecessary DOM writes
          let newOpacity = 1 - scrollTop / 500;

          // Clamp to [0, 1]
          if (newOpacity < 0) newOpacity = 0;
          if (newOpacity > 1) newOpacity = 1;

          // Only write to DOM if value changed significantly (0.001 precision)
          if (Math.abs(newOpacity - lastOpacity) > 0.001) {
              header.style.opacity = newOpacity;
              lastOpacity = newOpacity;
          } else if (newOpacity === 0 && lastOpacity !== 0) {
              // Ensure we hit exactly 0
              header.style.opacity = 0;
              lastOpacity = 0;
          } else if (newOpacity === 1 && lastOpacity !== 1) {
              // Ensure we hit exactly 1
              header.style.opacity = 1;
              lastOpacity = 1;
          }

          ticking = false;
        });

        ticking = true;
      }
    });
  }
})();
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

(function() {
    'use strict';

    // ⚡ Bolt: Use IntersectionObserver instead of scroll event for better performance
    const stickyCta = document.querySelector('.sticky-cta');
    const heroSection = document.querySelector('.landing-hero');

    if (stickyCta && heroSection) {
        // ⚡ Bolt: Use IntersectionObserver to avoid layout thrashing on scroll
        const observer = new IntersectionObserver((entries) => {
            const entry = entries[0];
            // Show sticky CTA when user scrolls past hero (not intersecting and above viewport)
            if (!entry.isIntersecting && entry.boundingClientRect.top < 0) {
                stickyCta.classList.remove('hidden');
                stickyCta.style.display = 'block';
            } else {
                stickyCta.classList.add('hidden');
                stickyCta.style.display = 'none';
            }
        }, {
            threshold: 0
        });

        observer.observe(heroSection);
    }

    // Form Validation and Submission
    const form = document.getElementById('lead-form');

    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            // Clear previous errors
            const errorGroups = form.querySelectorAll('.form-group.has-error, .checkbox-group.has-error');
            errorGroups.forEach(g => {
                g.classList.remove('has-error');
                // Reset aria-invalid for inputs in this group
                const inputs = g.querySelectorAll('input, select, textarea');
                inputs.forEach(input => input.setAttribute('aria-invalid', 'false'));
            });

            // Clear general error messages
            const generalErrors = form.querySelectorAll('.form-group > .error-msg');
            generalErrors.forEach(e => {
                 if (e.parentNode === form || e.parentNode.classList.contains('form-group-row') === false) {
                     e.textContent = '';
                 }
            });


            let isValid = true;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            // Helper for required fields
            const requiredFields = ['first_name', 'last_name', 'role', 'email', 'grade', 'goal'];
            requiredFields.forEach(field => {
                if (!data[field] || data[field].trim() === '') {
                    showError(field, 'This field is required');
                    isValid = false;
                }
            });

            // Validate Email
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (data.email && !emailRegex.test(data.email)) {
                showError('email', 'Please enter a valid email');
                isValid = false;
            }

            // Validate Consent
            if (!form.querySelector('#consent').checked) {
                const group = form.querySelector('#consent').closest('.checkbox-group');
                group.classList.add('has-error');
                showError('consent', 'This field is required');
                isValid = false;
            }

            if (!isValid) return;

            // Submit
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';

            const apiUrl = form.getAttribute('data-api-url');
            const siteKey = form.getAttribute('data-recaptcha-sitekey');

            try {
                if (typeof trackLeadSubmit === 'function') {
                    trackLeadSubmit();
                }

                // Execute ReCAPTCHA
                let token = '';
                if (window.grecaptcha && siteKey) {
                    await new Promise(resolve => grecaptcha.enterprise.ready(resolve));
                    token = await grecaptcha.enterprise.execute(siteKey, {action: 'landing_lead'});
                } else {
                    console.warn('ReCAPTCHA not loaded or site key missing');
                }

                // Prepare Payload
                const payload = {
                    ...data,
                    token: token,
                    action: 'landing_lead'
                };

                // Handle checkbox separately if needed, but FormData handles it (on/off).
                // We want boolean true for backend? Or just presence.
                // standard FormData gives 'on' if checked.
                payload.consent = true;

                const response = await fetch(`${apiUrl}/lead`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                     // Show success state
                    form.innerHTML = '<div class="success-message"><h2>Thanks!</h2><p>We will be in touch shortly.</p></div>';
                } else {
                    throw new Error('Network response was not ok');
                }

            } catch (error) {
                console.error('Submission error:', error);
                 // Fallback for demo/error handling - usually show error message
                 // reusing the success message logic from original file for now as a safe fallback?
                 // No, let's show an error.
                 const errorDiv = form.querySelector('.form-group:last-of-type .error-msg');
                 if(errorDiv) {
                     errorDiv.textContent = "Something went wrong. Please try again or contact us directly.";
                 } else {
                     alert("Something went wrong. Please try again.");
                 }
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            }
        });
    }

    function showError(fieldName, message) {
        const input = form.querySelector(`[name="${fieldName}"]`);
        if (input) {
            const group = input.closest('.form-group') || input.closest('.checkbox-group');
            if (group) {
                group.classList.add('has-error');
                input.setAttribute('aria-invalid', 'true');
                const errorDisplay = group.querySelector('.error-msg');
                if (errorDisplay) {
                    errorDisplay.textContent = message;
                }
            }
        }
    }

})();
