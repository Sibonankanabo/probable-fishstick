document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email, password: password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = '/dashboard'; // Redirect to dashboard
        } else {
            document.getElementById('error-message').textContent = 'Invalid credentials';
        }
    } catch (error) {
        document.getElementById('error-message').textContent = 'An error occurred';
    }
});

document.getElementById('registerForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const data = {
        fname: document.getElementById('fname').value,
        lname: document.getElementById('lname').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
        phone: document.getElementById('phone').value
    };

    try {
        const response = await fetch('/create_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        const messageDiv = document.getElementById('message');

        if (response.ok) {
            messageDiv.textContent = result.message;
            messageDiv.style.color = 'green';
        } else {
            messageDiv.textContent = result.error;
            messageDiv.style.color = 'red';
        }
    } catch (error) {
        console.error('Error:', error);
    }
});