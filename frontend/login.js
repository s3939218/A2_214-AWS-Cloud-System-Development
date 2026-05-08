const API_URL = "http://54.226.71.206";

async function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  const res = await fetch(`${API_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();

  if (data.success) {
    // store both username and email separately - subscription table uses email as key - s3874656
    localStorage.setItem("username", data.username);
    localStorage.setItem("email", data.email);
    window.location.href = "main.html";
  } else {
    // fixed capitalisation to match exact spec wording - s3874656
    document.getElementById("error").innerText = "email or password is invalid";
  }
}