// session check - redirect to login if not authenticated
if (!localStorage.getItem("email")) {
  window.location.href = "login.html";
}

const userElement = document.getElementById("user");
if (userElement) {
  userElement.innerText = localStorage.getItem("username");
}

// Logout
function logout() {
  localStorage.removeItem("username");
  localStorage.removeItem("email");
  window.location.href = "login.html";
}

// Search
async function search() {
  const title = document.getElementById("title").value;
  const artist = document.getElementById("artist").value;
  const year = document.getElementById("year").value;
  const album = document.getElementById("album").value;

  if (!title && !artist && !year && !album) {
    document.getElementById("results").innerHTML = "Please enter at least one search field.";
    return;
  }

  const res = await fetch("YOUR_API_URL/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, artist, year, album })
  });

  const data = await res.json();

  const container = document.getElementById("results");
  container.innerHTML = "";

  if (data.length === 0) {
    container.innerHTML = "No result is retrieved. Please query again";
    return;
  }

  data.forEach(song => {
    container.innerHTML += `
      <div style="border:1px solid #ccc; padding:10px; margin:10px;">
        <p><b>${song.title}</b> - ${song.artist}</p>
        <p>${song.album} (${song.year})</p>
        <img src="${song.image_url}" width="100"><br>
        <button onclick='subscribe(${JSON.stringify(song)})'>Subscribe</button>
      </div>
    `;
  });
}

// Subscribe
async function subscribe(song) {
  await fetch("YOUR_API_URL/subscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: localStorage.getItem("email"),
      song: song
    })
  });

  alert("Subscribed!");
  loadSubscriptions();
}

if (document.getElementById("subscriptions")) {
  loadSubscriptions();
}

async function loadSubscriptions() {
  const res = await fetch("YOUR_API_URL/subscriptions?email=" + localStorage.getItem("email"));
  const data = await res.json();

  const container = document.getElementById("subscriptions");
  container.innerHTML = "";

  data.forEach(song => {
    container.innerHTML += `
      <div style="border:1px solid green; padding:10px; margin:10px;">
        <p><b>${song.title}</b> - ${song.artist}</p>
        <img src="${song.image_url}" width="100"><br>
        <button onclick='removeSong(${JSON.stringify(song)})'>Remove</button>
      </div>
    `;
  });
}

async function removeSong(song) {
  await fetch("YOUR_API_URL/remove", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: localStorage.getItem("email"),
      song: song
    })
  });

  alert("Removed!");
  loadSubscriptions();
}