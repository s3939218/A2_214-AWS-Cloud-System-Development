const API = CONFIG.API;

// session check - redirect to login if not authenticated
if (!localStorage.getItem("email")) {
  window.location.href = "login.html";
}

const userElement = document.getElementById("user");

if (userElement) {
  // display username from localStorage
  userElement.innerText = localStorage.getItem("username");
}

// Logout
function logout() {
  // clear both username and email on logout
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

  // at least one field required
  if (!title && !artist && !year && !album) {
    document.getElementById("results").innerHTML =
      "Please enter at least one search field.";
    return;
  }

  const res = await fetch(API + "/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, artist, year, album })
  });

  const data = await res.json();

  const container = document.getElementById("results");
  container.innerHTML = "";

  if (data.length === 0) {
    container.innerHTML =
      "No result is retrieved. Please query again";
    return;
  }

  data.forEach(song => {

    // remove image_url before passing into onclick
    const songData = {
      title: song.title,
      artist: song.artist,
      year: song.year,
      album: song.album
    };

    container.innerHTML += `
      <div class="card">
        <img src="${song.image_url}" width="100">

        <div>
          <p><b>${song.title}</b> - ${song.artist}</p>
          <p>${song.album} (${song.year})</p>

          <button onclick='subscribe(${JSON.stringify(songData)})'>
            ➕ Subscribe
          </button>
        </div>
      </div>
    `;
  });
}

// Subscribe
async function subscribe(song) {

  await fetch(API + "/subscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },

    body: JSON.stringify({
      email: localStorage.getItem("email"),
      song: song
    })
  });

  alert("Subscribed!");

  // refresh subscriptions
  loadSubscriptions();
}

// Auto load subscriptions
if (document.getElementById("subscriptions")) {
  loadSubscriptions();
}

async function loadSubscriptions() {

  const res = await fetch(
    API + "/subscriptions?email=" +
    localStorage.getItem("email")
  );

  const data = await res.json();

  const container =
    document.getElementById("subscriptions");

  container.innerHTML = "";

  data.forEach(song => {

    container.innerHTML += `
      <div class="card">

        <img src="${song.image_url}" width="100">

        <div>
          <p><b>${song.title}</b> - ${song.artist}</p>
          <p>${song.album} (${song.year})</p>

          <button onclick='removeSong(${JSON.stringify({
            title: song.title,
            artist: song.artist,
            year: song.year,
            album: song.album
          })})'>
            ❌ Remove
          </button>
        </div>

      </div>
    `;
  });
}

// Remove subscription
async function removeSong(song) {

  await fetch(API + "/remove", {
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