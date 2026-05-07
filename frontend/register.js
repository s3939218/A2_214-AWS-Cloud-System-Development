async function register() {
  const email = document.getElementById("email").value;
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const res = await fetch("https://6ytigq2t1f.execute-api.us-east-1.amazonaws.com/prod/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password })
  });

  const data = await res.json();

  if (data.exists) {
    document.getElementById("msg").innerText = "The email already exists";
  } else {
    alert("Registered successfully");
    window.location.href = "login.html";
  }
}