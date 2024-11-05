function showLoginModal() {
    document.getElementById('loginModal').style.display = 'block';
}

function closeLoginModal() {
    document.getElementById('loginModal').style.display = 'none';
}

async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();
    if (data.success) {
        document.cookie = `session=${data.sessionToken}; path=/;`;
        document.getElementById('folderName').style.display = 'block';  // Show folder input
        document.getElementById('loginMessage').innerText = "Login successful!";
        closeLoginModal();  // Close modal
    } else {
        document.getElementById('loginMessage').innerText = "Login failed. Try again.";
    }
}

