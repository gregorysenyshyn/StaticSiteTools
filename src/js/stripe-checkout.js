// Stripe Checkout Logic
// Wrapped in IIFE to avoid global scope pollution
(function() {
    let stripe;
    let elements;
    let paymentElement;

    document.addEventListener('DOMContentLoaded', async () => {
        // Initialize Stripe if key is present
        // The key is injected via data attribute on the body or a script tag,
        // but for this specific setup, we'll assume the button carries the necessary config or we fetch it.
        // Actually, we need the public key. I will assume it's available via a global variable or I can fetch it?
        // Plan: The button will trigger the flow. The key might be hardcoded in the built JS or fetched.
        // Since I'm using `data.yaml` variables, I can't easily inject them into JS without a build step that does replacement.
        // CHECK: The SST build system doesn't seem to do variable replacement in JS files based on `data.yaml`?
        // Wait, `landing-form.html` uses data attributes: `data-api-url`, `data-recaptcha-sitekey`.
        // I should follow that pattern. I'll add the config to the modal container or the button.

        const modal = document.getElementById('payment-modal');
        if (!modal) return; // Not on a page with checkout

        const closeBtn = modal.querySelector('.neo-close-btn');
        const form = document.getElementById('payment-form');
        const submitBtn = document.getElementById('payment-submit');
        const messageDiv = document.getElementById('payment-message');
        const spinner = document.getElementById('payment-spinner');
        const buttonText = document.getElementById('button-text');

        // Config from data attributes on the modal container
        const stripeKey = modal.getAttribute('data-stripe-key');
        const apiUrl = modal.getAttribute('data-api-url');

        if (!stripeKey || !apiUrl) {
            console.error('Stripe configuration missing.');
            return;
        }

        stripe = Stripe(stripeKey);

        // Open Modal Handler
        document.querySelectorAll('.enroll-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const priceId = btn.getAttribute('data-stripe-price-id');
                if (!priceId) return;

                openModal();
                await initializePayment(priceId, apiUrl);
            });
        });

        // Close Modal Handlers
        closeBtn.addEventListener('click', closeModal);
        window.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        // Submit Handler
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            setLoading(true);

            const { error } = await stripe.confirmPayment({
                elements,
                confirmParams: {
                    // Make sure to change this to your payment completion page
                    return_url: window.location.origin + '/landing/success',
                },
            });

            // This point will only be reached if there is an immediate error when
            // confirming the payment. Otherwise, your customer will be redirected to
            // your `return_url`.
            if (error.type === "card_error" || error.type === "validation_error") {
                showMessage(error.message);
            } else {
                showMessage("An unexpected error occurred.");
            }

            setLoading(false);
        });

        function openModal() {
            modal.style.display = 'flex'; // or add class 'show' if using CSS transitions
            modal.classList.add('show');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }

        function closeModal() {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = 'none';
                document.body.style.overflow = '';
                // Optional: Destroy elements to reset state?
                // if (elements) elements = undefined;
                // document.getElementById('payment-element').innerHTML = '';
            }, 100);
        }

        async function initializePayment(priceId, apiUrl) {
            // clear previous
            // if (elements) ...

            // Fetch Client Secret
            // The backend needs to create a PaymentIntent.
            // We pass the priceId so the backend knows the amount.
            try {
                const response = await fetch(`${apiUrl}/create-payment-intent`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ priceId }),
                });

                if (!response.ok) {
                    throw new Error('Failed to initialize payment');
                }

                const { clientSecret } = await response.json();

                const appearance = {
                    theme: 'flat',
                    variables: {
                        colorPrimary: '#284B99',
                        colorBackground: '#ffffff',
                        colorText: '#000000',
                        fontFamily: 'Helvetica, Arial, sans-serif',
                        borderRadius: '0px', // Brutalist
                    },
                    rules: {
                        '.Input': {
                            border: '3px solid #000',
                            boxShadow: '4px 4px 0px #000',
                        },
                        '.Input:focus': {
                            boxShadow: '6px 6px 0px #000',
                        }
                    }
                };

                elements = stripe.elements({ appearance, clientSecret });

                const paymentElementOptions = {
                    layout: "tabs",
                };

                paymentElement = elements.create("payment", paymentElementOptions);
                paymentElement.mount("#payment-element");

            } catch (e) {
                console.error(e);
                showMessage("Failed to load payment system.");
            }
        }

        function showMessage(messageText) {
            messageDiv.style.display = "block";
            messageDiv.textContent = messageText;
            setTimeout(() => {
                messageDiv.style.display = "none";
                messageDiv.textContent = "";
            }, 5000);
        }

        function setLoading(isLoading) {
            if (isLoading) {
                submitBtn.disabled = true;
                spinner.style.display = "block";
                buttonText.style.display = "none";
            } else {
                submitBtn.disabled = false;
                spinner.style.display = "none";
                buttonText.style.display = "block";
            }
        }
    });
})();
