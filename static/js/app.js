
const $ = (id) => document.getElementById(id);

let currentUser = null;
let selectedMaterialId = null;

// SHOW SUCCESS OR ERROR MESSAGE
function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.remove("hidden");

  setTimeout(() => el.classList.add("hidden"), 3200);
}

// API CONNECTION
async function api(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.error || data.message || `Request failed (${response.status})`
    );
  }

  return data;
}

// FORM DATA
function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

// HTML SECURITY
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[c]));
}


// LOGIN STATUS UI
function authUI() {
  $("auth-status").innerHTML = currentUser
    ? `<span class="muted">Hi, ${escapeHtml(currentUser.name)}</span>
       <button class="btn outline" id="logout-btn">Logout</button>`
    : `<button class="btn outline" id="show-auth">Login / Register</button>`;

  const logout = $("logout-btn");
  if (logout) logout.onclick = logoutUser;

  const show = $("show-auth");
  if (show) {
    show.onclick = () => {
      $("auth-panel").classList.remove("hidden");
    };
  }
}


// LOAD LOGGED-IN USER
async function loadUser() {
  try {
    currentUser = await api("/api/me");
  } catch {
    currentUser = null;
  }

  authUI();
}


// LOAD MARKETPLACE MATERIALS
async function loadMaterials(search = "") {
  try {
    const rows = await api(
      `/api/materials?search=${encodeURIComponent(search)}`
    );

    $("material-count").textContent = rows.length;

    $("materials").innerHTML = rows.length
      ? rows.map(m => `
        <article class="material-card">

          <span class="tag">${escapeHtml(m.category)}</span>

          <h3>${escapeHtml(m.title)}</h3>

          <p class="material-meta">
            ${escapeHtml(m.description || "No description provided.")}
          </p>

          <p>
            <b>${m.quantity} ${escapeHtml(m.unit)}</b>
            · ${escapeHtml(m.condition)}
          </p>

          <p class="material-meta">
            ⌖ ${escapeHtml(m.location)}
            · ${m.is_free ? "Free" : "₹" + Number(m.price).toFixed(2)}
          </p>

          <button
            class="btn request-btn"
            data-id="${m.material_id}">
            Request material
          </button>

        </article>
      `).join("")
      : `<p class="muted">
          No materials listed yet. Login and add the first listing.
        </p>`;

    document.querySelectorAll(".request-btn").forEach(button => {
      button.onclick = () =>
        requestMaterial(Number(button.dataset.id));
    });

  } catch (e) {
    $("materials").textContent = e.message;
  }
}


// OPEN REQUEST MATERIAL POPUP
function requestMaterial(materialId) {

  if (!currentUser) {
    toast("Please login before requesting a material.");

    $("auth-panel").classList.remove("hidden");
    return;
  }

  selectedMaterialId = materialId;

  $("request-form").reset();

  $("request-modal").classList.remove("hidden");
}


// SUBMIT MATERIAL REQUEST
$("request-form").addEventListener("submit", async (event) => {

  event.preventDefault();

  const quantity = Number($("request-quantity").value);
  const message = $("request-message").value;

  if (!selectedMaterialId || quantity <= 0) {
    toast("Please enter a valid quantity.");
    return;
  }

  try {

    await api("/api/requests", {
      method: "POST",

      body: JSON.stringify({
        material_id: selectedMaterialId,
        requested_quantity: quantity,
        message: message
      })
    });

    $("request-modal").classList.add("hidden");

    selectedMaterialId = null;

    toast("Request submitted successfully!");

    loadRequests();
    loadNotifications();

  } catch (error) {

    toast(error.message);

    if (
      error.message.toLowerCase().includes("login required") ||
      error.message.includes("401")
    ) {
      $("request-modal").classList.add("hidden");
      currentUser = null;
      authUI();
      $("auth-panel").classList.remove("hidden");
    }
  }
});


// CANCEL REQUEST POPUP
$("cancel-request").onclick = () => {

  $("request-modal").classList.add("hidden");

  selectedMaterialId = null;
};


// LOGIN FUNCTION
async function loginUser(event) {

  event.preventDefault();

  try {

    await api("/api/login", {
      method: "POST",
      body: JSON.stringify(formData(event.target))
    });

    event.target.reset();

    await loadUser();

    $("auth-panel").classList.add("hidden");

    toast("Login successful.");

    loadRequests();
    loadImpact();
    loadNotifications();

  } catch (e) {
    toast(e.message);
  }
}


// REGISTER FUNCTION
async function registerUser(event) {

  event.preventDefault();

  try {

    await api("/api/register", {
      method: "POST",
      body: JSON.stringify(formData(event.target))
    });

    event.target.reset();

    toast("Registration successful. Please login.");

  } catch (e) {
    toast(e.message);
  }
}


// LOGOUT FUNCTION
async function logoutUser() {

  try {

    await api("/api/logout", {
      method: "POST"
    });

    currentUser = null;

    authUI();

    toast("Logged out.");

    loadRequests();

  } catch (e) {
    toast(e.message);
  }
}


// ADD MATERIAL FUNCTION
async function addMaterial(event) {

  event.preventDefault();

  if (!currentUser) {

    toast("Please login first.");

    $("auth-panel").classList.remove("hidden");

    return;
  }

  const data = formData(event.target);

  data.quantity = Number(data.quantity);
  data.price = Number(data.price || 0);

  data.is_free = event.target.elements.is_free.checked;

  try {

    await api("/api/materials", {
      method: "POST",
      body: JSON.stringify(data)
    });

    event.target.reset();

    toast("Material listed successfully.");

    loadMaterials();

  } catch (e) {
    toast(e.message);
  }
}


// LOAD SENT AND RECEIVED REQUESTS
async function loadRequests() {

  if (!currentUser) {

    $("sent-requests").textContent =
      "Login to view your requests.";

    $("received-requests").textContent =
      "Login to view incoming requests.";

    return;
  }

  try {

    const [sent, received] = await Promise.all([
      api("/api/requests"),
      api("/api/requests/received")
    ]);

    // SENT REQUESTS
    $("sent-requests").innerHTML = sent.length
      ? sent.map(r => `
        <div class="list-item">

          Request #${r.request_id}
          · Material #${r.material_id}

          <p>
            ${r.requested_quantity} requested
            · <b>${escapeHtml(r.status)}</b>
          </p>

        </div>
      `).join("")
      : "No requests sent yet.";


    // RECEIVED REQUESTS
    $("received-requests").innerHTML = received.length
      ? received.map(r => `
        <div class="list-item">

          Request #${r.request_id}
          · Material #${r.material_id}

          <p>
            ${r.requested_quantity} requested
            · <b>${escapeHtml(r.status)}</b>
          </p>

          ${
            r.status === "pending"
              ? `
                <div class="actions">

                  <button
                    class="btn small accept"
                    data-id="${r.request_id}"
                    data-status="accepted">
                    Accept
                  </button>

                  <button
                    class="btn outline small accept"
                    data-id="${r.request_id}"
                    data-status="rejected">
                    Reject
                  </button>

                </div>
              `
              : ""
          }

        </div>
      `).join("")
      : "No incoming requests.";


    // ACCEPT AND REJECT BUTTONS
    document.querySelectorAll(".accept").forEach(button => {

      button.onclick = () => {

        updateRequest(
          Number(button.dataset.id),
          button.dataset.status
        );

      };

    });

  } catch (e) {
    toast(e.message);
  }
}


// ACCEPT OR REJECT REQUEST
async function updateRequest(id, status) {

  try {

    await api(`/api/requests/${id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status })
    });

    toast(`Request ${status}.`);

    loadRequests();
    loadNotifications();

  } catch (e) {
    toast(e.message);
  }
}


// LOAD ENVIRONMENTAL IMPACT
async function loadImpact() {

  if (!currentUser) return;

  try {

    const data = await api("/api/impact");

    $("total-reused").textContent =
      Number(data.total_quantity_reused).toFixed(2);

    $("record-count").textContent =
      data.total_records;

    $("impact-count").textContent =
      data.total_records;

  } catch (e) {
    toast(e.message);
  }
}


// LOAD NOTIFICATIONS
async function loadNotifications() {

  if (!currentUser) return;

  try {

    const rows = await api("/api/notifications");

    $("notifications").innerHTML = rows.length
      ? rows.map(n => `
        <div class="list-item">

          ${escapeHtml(n.message)}

          <span class="material-meta">
            ${n.is_read ? " · Read" : " · Unread"}
          </span>

        </div>
      `).join("")
      : "No notifications yet.";

  } catch (e) {
    toast(e.message);
  }
}


// EVENT LISTENERS
$("login-form").addEventListener("submit", loginUser);

$("register-form").addEventListener("submit", registerUser);

$("material-form").addEventListener("submit", addMaterial);

$("close-auth").onclick = () => {
  $("auth-panel").classList.add("hidden");
};

$("search-form").addEventListener("submit", event => {

  event.preventDefault();

  loadMaterials(formData(event.target).search);

});

$("refresh-requests").onclick = loadRequests;

$("load-impact").onclick = loadImpact;

$("load-notifications").onclick = loadNotifications;


// INITIALIZE APPLICATION
(async function init() {

  await loadUser();

  await loadMaterials();

  await loadRequests();

  await loadImpact();

  await loadNotifications();

})();
