(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('registration-form');
        if (!form) return;

        // 1. Parse payment_id from URL
        const urlParams = new URLSearchParams(window.location.search);
        const paymentId = urlParams.get('payment_id');
        const apiUrl = form.getAttribute('data-api-url');
        const submitBtn = form.querySelector('button[type="submit"]');
        const messageDiv = document.getElementById('form-message');

        // Disable button initially
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.title = "Valid payment required";
        }

        const showPurchaseError = () => {
            if (messageDiv) {
                messageDiv.innerHTML = 'We\'re having trouble locating your purchase. Please email <a href="mailto:contact@asyncacademy.ca">contact@asyncacademy.ca</a>, and we\'ll get everything sorted out!';
                messageDiv.className = "error-msg";
                messageDiv.style.display = "block";
            }
        };

        if (paymentId) {
            document.getElementById('payment_id').value = paymentId;

            // Fetch registration details
            fetch(`${apiUrl}/registration-details?payment_id=${paymentId}`)
                .then(response => {
                    if (response.ok) return response.json();
                    throw new Error("Failed to fetch registration details");
                })
                .then(data => {
                    // Valid payment found, enable button
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.title = "";
                    }

                    if (data.course_name) {
                        const contextDiv = document.getElementById('registration-context');
                        const courseNameP = document.getElementById('context-course-name');
                        if (contextDiv && courseNameP) {
                            courseNameP.textContent = data.course_name;
                            contextDiv.style.display = 'block';
                        }
                    }
                    if (data.email) {
                        const emailInput = document.getElementById('student_email');
                        if (emailInput) {
                            emailInput.value = data.email;
                            // Also prefill parent email as a convenience? Maybe not always desirable.
                            // But usually the payer is the parent.
                            const parentEmailInput = document.getElementById('parent_email');
                            if (parentEmailInput && !parentEmailInput.value) {
                                parentEmailInput.value = data.email;
                            }
                        }
                    }
                })
                .catch(err => {
                    console.log("Could not load registration context", err);
                    showPurchaseError();
                });

        } else {
            showPurchaseError();
        }

        // 2. Form Submission Handler
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const submitBtn = form.querySelector('button[type="submit"]');
            const messageDiv = document.getElementById('form-message');
            const originalBtnText = submitBtn.textContent;

            // Basic Client-side Validation (HTML5 'required' handles most)
            // Can add more custom validation here if needed.

            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
            messageDiv.textContent = '';
            messageDiv.className = '';

            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            const apiUrl = form.getAttribute('data-api-url');

            try {
                const response = await fetch(`${apiUrl}/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    messageDiv.textContent = "Registration successful! You will receive a confirmation email shortly.";
                    messageDiv.className = "success-message";
                    form.reset();
                    // Optionally hide form
                    // form.style.display = 'none';
                } else {
                    const resData = await response.json();
                    throw new Error(resData.error || 'Registration failed');
                }
            } catch (error) {
                console.error('Registration Error:', error);
                messageDiv.textContent = `Error: ${error.message}`;
                messageDiv.className = "error-msg";
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            }
        });
    });
})();
