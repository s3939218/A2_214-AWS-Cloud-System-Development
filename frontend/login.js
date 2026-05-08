const API = CONFIG.API;

async function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  console.log("Sending:", { email, password });

  const res = await fetch(API + "/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  console.log("Response status:", res.status);

  const data = await res.json();
  console.log("Response data:", data);

  if (data.success) {
    // store both username and email separately
    localStorage.setItem("username", data.username);
    localStorage.setItem("email", data.email);

    window.location.href = "main.html";
  } else {
    document.getElementById("error").innerText =
      "email or password is invalid";
  }
}