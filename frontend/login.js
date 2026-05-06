async function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  const res = await fetch("YOUR_API_URL/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();

  if (data.success) {
    localStorage.setItem("user", data.username);
    window.location.href = "main.html";
  } else {
    document.getElementById("error").innerText = "Email or password is invalid";
  }
}
