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
