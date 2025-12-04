// Redirect if not logged in
if (!localStorage.getItem("lnt_user")) {
  window.location.href = "login.html";
}
// --- TAB SWITCHING ---
document.querySelectorAll(".nav li").forEach((tab) => {
  tab.addEventListener("click", () => {
    // Highlight selected tab
    document.querySelector(".nav li.active")?.classList.remove("active");
    tab.classList.add("active");

    // Hide all tab content
    document.querySelectorAll(".tab-content").forEach((sec) => {
      sec.style.display = "none";
      sec.classList.remove("active");
    });

    // Show the selected tab section
    const target = tab.dataset.tab;
    const content = document.getElementById("tab-" + target);
    if (content) {
      content.style.display = "block";
      content.classList.add("active");
    }
  });
});

//********************************
/*********************************
// *****THIS IS FOR THE JOBS TAB
/*********************************
 * *****************************
 */
async function fetchJobsFromBackend() {
  try {
    const resp = await fetch("http://localhost:8000/test/status");
    if (!resp.ok) {
      throw new Error(`Backend responded with ${resp.status}`);
    }

    const data = await resp.json();
    const tests = data.tests || {};

    // Convert { "1": {...}, "2": {...} } to an array of job objects
    const jobs = Object.entries(tests).map(([id, t]) => ({
      id: Number(id),
      name: t.name || `Test ${id}`,
      description: t.description || "",
      status: (t.status || "unknown").toLowerCase(),
      started_at: t.started_at || null,
      finished_at: t.finished_at || null,
      test_duration: t.test_duration || null,
      logs: t.logs || [],
      serial_logs: t.serial_logs || {},
      serial_streams: t.serial_streams || {},
    }));

    return jobs;
  } catch (err) {
    console.error("Error fetching jobs from backend:", err);
    return [];
  }
}

async function updateJobs() {
  const container = document.getElementById("jobsContainer");
  if (!container) return;

  container.innerHTML = "";

  const jobs = await fetchJobsFromBackend();

  if (jobs.length === 0) {
    const empty = document.createElement("p");
    empty.textContent = "No jobs found.";
    empty.style.padding = "10px 5px";
    container.appendChild(empty);
    return;
  }

  jobs.forEach((job) => {
    const card = document.createElement("div");
    card.classList.add("job-card");

    // --- Header row (title + status dot) ---
    const header = document.createElement("div");
    header.classList.add("job-header");

    const title = document.createElement("div");
    title.classList.add("job-title");
    title.textContent = `${job.id} - ${job.name}`;

    const statusDot = document.createElement("span");
    statusDot.classList.add("job-status-dot", `job-${job.status}`);

    header.appendChild(title);
    header.appendChild(statusDot);
    card.appendChild(header);

    // --- Description (optional) ---
    if (job.description) {
      const desc = document.createElement("p");
      desc.classList.add("job-description");
      desc.textContent = job.description;
      card.appendChild(desc);
    }

    // --- Timing line ---
    const meta = document.createElement("div");
    meta.classList.add("job-meta");
    const startText = job.started_at
      ? new Date(job.started_at).toLocaleString()
      : "unknown";
    const durationText = job.test_duration || "";
    meta.textContent =
      `Started: ${startText}` +
      (durationText ? ` · Duration: ${durationText}` : "");
    card.appendChild(meta);

    // Click → open detail view (we'll reuse your existing openJobView)
    card.addEventListener("click", () => openJobView(job));

    container.appendChild(card);
  });
}
// ====== JOB DETAIL VIEW PLACEHOLDER ======
function openJobView(job) {
  // Hide job list and show detail view
  document.getElementById("tab-jobs").style.display = "none";
  document.getElementById("jobDetailView").style.display = "block";

  // Job name + number + status icon
  document.getElementById(
    "jobDetailTitle"
  ).textContent = `${job.id} - ${job.name}`;
  document.getElementById(
    "jobDetailStatus"
  ).className = `job-status job-${job.status}`;

  // Description
  document.getElementById("jobDetailDescription").textContent =
    job.description || "";

  // ---- LOGS ----
  const logList = document.getElementById("logFileList");
  logList.innerHTML = "";

  (job.logs || []).forEach((logLine) => {
    const li = document.createElement("li");
    li.textContent = logLine;
    logList.appendChild(li);
  });

  // ---- STREAM DATA ----
  const streamNameEl = document.getElementById("streamName");
  const streamBox = document.getElementById("streamBox");
  streamBox.innerHTML = "";

  const streams = job.serial_streams || {};
  const hosts = Object.keys(streams);

  if (hosts.length === 0) {
    // No stream data for this job
    streamNameEl.textContent = "No stream data";
    streamBox.textContent = "";
  } else {
    // For now, just show the first host's streams
    const host = hosts[0];
    streamNameEl.textContent = host;

    const hostStreams = streams[host];
    let lines = [];

    if (Array.isArray(hostStreams)) {
      // If backend gave a simple list of lines
      lines = hostStreams;
    } else if (typeof hostStreams === "object" && hostStreams !== null) {
      // If backend gave an object like { varName: [lines] } or { varName: "..." }
      for (const [key, value] of Object.entries(hostStreams)) {
        if (Array.isArray(value)) {
          lines.push(`${key}: ${value.join(" ")}`);
        } else {
          lines.push(`${key}: ${String(value)}`);
        }
      }
    } else if (hostStreams != null) {
      lines = [String(hostStreams)];
    }

    streamBox.innerHTML = lines.join("<br>");
  }

  // Scroll controls
  document.getElementById("scrollUp").onclick = () => {
    streamBox.scrollTop -= 40;
  };
  document.getElementById("scrollDown").onclick = () => {
    streamBox.scrollTop += 40;
  };
}

//*****************************************
/******************************************
// *****THIS IS FOR THE MANAGEMENT TAb****
/*****************************************
 * ***************************************
 */

async function removeHost(hostname) {
  try {
    const url = `http://localhost:8000/device/remove?hostname=${encodeURIComponent(
      hostname
    )}`;

    const response = await fetch(url, { method: "POST" });

    if (!response.ok) {
      console.error("Failed to remove host:", response.status);
      alert("Error removing host — check backend.");
      return;
    }

    const data = await response.json();
    console.log("Host removed:", data);

    // Refresh both host lists
    updateDevices();
  } catch (err) {
    console.error("Error removing host:", err);
  }
}
// ====== MANAGEMENT TAB: ADD HOST ======
async function addHost(hostname, ipAddress) {
  try {
    const url = `http://localhost:8000/device/add?hostname=${encodeURIComponent(
      hostname
    )}&ip_address=${encodeURIComponent(ipAddress)}`;

    const response = await fetch(url, {
      method: "POST",
    });

    const msg = document.getElementById("addHostMessage");

    if (!response.ok) {
      if (msg) {
        msg.textContent = "Error adding host. Check backend.";
        msg.style.color = "red";
      }
      console.error("Backend returned status", response.status);
      return;
    }

    const data = await response.json();
    console.log("Add host response:", data);

    if (msg) {
      msg.textContent = `Host "${hostname}" added.`;
      msg.style.color = "green";
    }

    // Refresh Hosts + Management lists
    updateDevices();
  } catch (err) {
    console.error(err);
    const msg = document.getElementById("addHostMessage");
    if (msg) {
      msg.textContent = "Error adding host. Check backend.";
      msg.style.color = "red";
    }
  }
}
///****************************************
// ****************************************
// ********Host and management*************
// ****************************************
// ********************************* */
async function updateDevices() {
  try {
    // Call backend instead of using mock data
    const response = await fetch("http://127.0.0.1:8000/device/list");
    if (!response.ok) {
      throw new Error("Failed to fetch device list");
    }

    const data = await response.json();

    const hosts = data.hosts || {};
    const list = document.getElementById("deviceList");
    if (!list) return;

    list.innerHTML = "";

    Object.entries(hosts).forEach(([hostname, host]) => {
      // --- HOST CONTAINER ---
      const groupDiv = document.createElement("div");
      groupDiv.classList.add("host-group");

      // Host title (pi-01, pi-02, etc.)
      const title = document.createElement("div");
      title.classList.add("host-title");
      title.textContent = hostname;
      groupDiv.appendChild(title);

      // Get DUTs from backend structure
      const duts = host.duts?.items || [];

      duts.forEach((dut) => {
        const li = document.createElement("li");
        li.classList.add("device-item");

        const span = document.createElement("span");
        span.classList.add("dut-text");

        // Example: "SN001 : running"
        span.textContent = `${dut.id} : ${dut.status}`;

        // Color by status (your CSS already defines .status-running, etc.)
        span.classList.add(`status-${dut.status}`);

        li.appendChild(span);
        groupDiv.appendChild(li);
      });

      list.appendChild(groupDiv);
    });

    // If you have a Management tab host list helper, keep it in sync:
    if (typeof refreshManagementHosts === "function") {
      refreshManagementHosts(hosts);
    }
  } catch (err) {
    console.error("Error in updateDevices:", err);
  }
}

document.getElementById("refreshBtn").addEventListener("click", updateDevices);
updateDevices();

// Hook up the form submit
const addHostForm = document.getElementById("addHostForm");
if (addHostForm) {
  addHostForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const nameInput = document.getElementById("hostNameInput");
    const ipInput = document.getElementById("hostIpInput");

    const hostname = nameInput.value.trim();
    const ipAddress = ipInput.value.trim();

    if (!hostname || !ipAddress) {
      const msg = document.getElementById("addHostMessage");
      if (msg) {
        msg.textContent = "Please fill in both fields.";
        msg.style.color = "red";
      }
      return;
    }

    addHost(hostname, ipAddress);
    // Optionally clear inputs
    nameInput.value = "";
    ipInput.value = "";
  });
}
// ====== MANAGEMENT TAB: HOST LIST ======
function refreshManagementHosts(hosts) {
  const list = document.getElementById("managementHostList");
  if (!list) return;

  list.innerHTML = "";

  Object.keys(hosts).forEach((hostname) => {
    const li = document.createElement("li");
    li.classList.add("device-item");

    const span = document.createElement("span");
    span.classList.add("dut-text");
    span.textContent = hostname;

    const delBtn = document.createElement("button");
    delBtn.classList.add("delete-host-btn");
    delBtn.textContent = "✖";
    delBtn.onclick = () => removeHost(hostname);

    li.appendChild(span);
    li.appendChild(delBtn);
    list.appendChild(li);
  });
}

// ====== STATISTICS TAB ======
async function updateStatistics() {
  const resp = await fetch("http://localhost:8000/test/stats");
  const stats = await resp.json();

  document.getElementById("statTotalJobs").textContent = stats.total_jobs;
  document.getElementById("statPassed").textContent = stats.passed;
  document.getElementById("statFailed").textContent = stats.failed;
  document.getElementById("statCanceled").textContent = stats.canceled;
  document.getElementById("statRunning").textContent = stats.running;

  document.getElementById("statTotalLogs").textContent = stats.total_logs;
  document.getElementById("statStreamVars").textContent =
    stats.total_stream_vars;
  document.getElementById("statTotalTestTime").textContent =
    stats.total_test_hours.toFixed(2) + " hrs";
}
function logoutUser() {
  localStorage.removeItem("lnt_user");
  localStorage.removeItem("lnt_role");
  window.location.href = "login.html";
}
//------------------------------------------
// USER MANAGEMENT FUNCTIONS
//------------------------------------------

async function loadUsers() {
  const listEl = document.getElementById("userList");
  listEl.innerHTML = "<li>Loading...</li>";

  try {
    const resp = await fetch("http://127.0.0.1:8000/user/list");
    const data = await resp.json();

    listEl.innerHTML = ""; // Clear old items

    data.users.forEach((username) => {
      const li = document.createElement("li");
      li.innerHTML = `
        ${username}
        <button class="delete-btn" onclick="removeUser('${username}')">✖</button>
      `;
      listEl.appendChild(li);
    });
  } catch (err) {
    listEl.innerHTML = "<li>Error loading users.</li>";
  }
}

async function addUser(event) {
  event.preventDefault();

  const username = document.getElementById("newUserName").value.trim();
  const password = document.getElementById("newUserPass").value.trim();
  const role = document.getElementById("newUserRole").value;
  const msg = document.getElementById("addUserMsg");

  if (!username || !password) {
    msg.textContent = "Username and password required.";
    msg.style.color = "red";
    return;
  }

  try {
    const resp = await fetch(
      `http://127.0.0.1:8000/user/add?username=${username}&password=${password}&role=${role}`,
      { method: "POST" }
    );

    if (!resp.ok) {
      const errorData = await resp.json();
      msg.textContent = errorData.detail || "Error adding user.";
      msg.style.color = "red";
      return;
    }

    msg.textContent = `User '${username}' added.`;
    msg.style.color = "green";

    loadUsers();
  } catch (err) {
    msg.textContent = "Network error.";
    msg.style.color = "red";
  }
}

async function removeUser(username) {
  if (!confirm(`Remove user '${username}'?`)) return;

  await fetch(`http://127.0.0.1:8000/user/remove?username=${username}`, {
    method: "POST",
  });

  loadUsers();
}
document.getElementById("addUserForm").addEventListener("submit", addUser);

document.getElementById("refreshBtn").addEventListener("click", updateDevices);
updateDevices();
updateJobs();
updateStatistics();
