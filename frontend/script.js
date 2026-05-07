const API_URL = "http://54.226.71.206";

// session check - redirect to login if not authenticated - s3874656
if (!localStorage.getItem("email")) {
  window.location.href = "login.html";
}

const userElement = document.getElementById("user");
if (userElement) {
  // display username from localStorage - s3874656
  userElement.innerText = localStorage.getItem("username");
}

// Logout
function logout() {
  // clear both username and email on logout - s3874656
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

  // at least one field required per assignment spec - s3874656
  if (!title && !artist && !year && !album) {
    document.getElementById("results").innerHTML = "Please enter at least one search field.";
    return;
  }

  const res = await fetch(`${API_URL}/search`, {
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
    // strip image_url from song data passed to subscribe - pre-signed URLs break onclick attributes - s3874656
    const songData = { title: song.title, artist: song.artist, year: song.year, album: song.album };
    container.innerHTML += `
      <div style="border:1px solid #ccc; padding:10px; margin:10px;">
        <p><b>${song.title}</b> - ${song.artist}</p>
        <p>${song.album} (${song.year})</p>
        <img src="${song.image_url}" width="100"><br>
        <button onclick='subscribe(${JSON.stringify(songData)})'>Subscribe</button>
      </div>
    `;
  });
}

// Subscribe
async function subscribe(song) {
  await fetch(`${API_URL}/subscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      // send email not username - subscription table uses email as key - s3874656
      email: localStorage.getItem("email"),
      song: song
    })
  });

  alert("Subscribed!");
  // refresh subscriptions immediately after subscribing - s3874656
  loadSubscriptions();
}

if (document.getElementById("subscriptions")) {
  loadSubscriptions();
}

async function loadSubscriptions() {
  // pass email as query parameter - backend reads email not user - s3874656
  const res = await fetch(`${API_URL}/subscriptions?email=` + localStorage.getItem("email"));
  const data = await res.json();

  const container = document.getElementById("subscriptions");
  container.innerHTML = "";

  data.forEach(song => {
    // strip image_url from song data passed to removeSong - pre-signed URLs break onclick attributes - s3874656
    container.innerHTML += `
      <div style="border:1px solid green; padding:10px; margin:10px;">
        <p><b>${song.title}</b> - ${song.artist}</p>
        <img src="${song.image_url}" width="100"><br>
        <button onclick='removeSong(${JSON.stringify({title: song.title, artist: song.artist, year: song.year, album: song.album})})'>Remove</button>
      </div>
    `;
  });
}

async function removeSong(song) {
  await fetch(`${API_URL}/remove`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      // send email not username - s3874656
      email: localStorage.getItem("email"),
      song: song
    })
  });

  alert("Removed!");
  loadSubscriptions();
}