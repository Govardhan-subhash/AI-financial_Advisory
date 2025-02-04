document.getElementById("registerForm")?.addEventListener("submit", async function (e) {
    e.preventDefault();
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !email || !password) {
        alert("All fields are required!");
        return;
    }

    const response = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
    });

    const data = await response.json();
    alert(data.message);

    if (response.ok) {
        window.location.href = "/login";  // Redirect to login page on success
    }
});


document.getElementById("loginForm")?.addEventListener("submit", async function (e) {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();
    alert(data.message);

    if (response.ok) {
        window.location.href = "/input";  // Redirect to dashboard after login
    }
});
