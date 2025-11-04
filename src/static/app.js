document.addEventListener("DOMContentLoaded", () => {
  loadActivities();

  document.getElementById("signup-form").addEventListener("submit", (e) => {
    e.preventDefault();
    signUpForActivity();
  });
});

// Load activities from the server
async function loadActivities() {
  try {
    const response = await fetch("/activities");
    const activities = await response.json();

    displayActivities(activities);
    populateActivitySelect(activities);
  } catch (error) {
    console.error("Error loading activities:", error);
    document.getElementById("activities-list").innerHTML =
      '<p class="error">Failed to load activities.</p>';
  }
}

// Display activities on the page
function displayActivities(activities) {
  const activitiesList = document.getElementById("activities-list");

  if (Object.keys(activities).length === 0) {
    activitiesList.innerHTML = "<p>No activities available.</p>";
    return;
  }

  const activitiesHtml = Object.entries(activities)
    .map(
      ([name, activity]) => `
        <div class="activity-card">
            <h4>${name}</h4>
            <p><strong>Description:</strong> ${activity.description}</p>
            <p><strong>Schedule:</strong> ${activity.schedule}</p>
            <p><strong>Capacity:</strong> ${activity.participants.length}/${activity.max_participants}</p>
            <div class="participants-section">
                <strong>Current Participants:</strong>
                ${activity.participants.length > 0 
                    ? `<ul class="participants-list">${activity.participants.map(email => `<li>${email}</li>`).join('')}</ul>`
                    : '<p class="no-participants">No participants yet</p>'
                }
            </div>
        </div>
    `
    )
    .join("");

  activitiesList.innerHTML = activitiesHtml;
}

// Populate the activity select dropdown
function populateActivitySelect(activities) {
  const activitySelect = document.getElementById("activity");
  const options = Object.keys(activities)
    .map(
      (name) => `<option value="${name}">${name}</option>`
    )
    .join("");

  activitySelect.innerHTML = "<option value="">-- Select an activity --</option>" + options;
}

// Sign up for an activity
async function signUpForActivity() {
  const email = document.getElementById("email").value;
  const activityName = document.getElementById("activity").value;
  const messageDiv = document.getElementById("message");

  if (!email || !activityName) {
    showMessage("Please fill in all fields.", "error");
    return;
  }

  try {
    const response = await fetch(
      `/activities/${encodeURIComponent(activityName)}/signup?email=${encodeURIComponent(
        email
      )}`,
      {
        method: "POST",
      }
    );

    const result = await response.json();

    if (response.ok) {
      showMessage(result.message, "success");
      document.getElementById("signup-form").reset();
      loadActivities(); // Refresh the activities list
    } else {
      showMessage(result.detail || "An error occurred", "error");
    }
  } catch (error) {
    console.error("Error signing up:", error);
    showMessage("Failed to sign up. Please try again.", "error");
  }
}

// Show a message to the user
function showMessage(message, type) {
  const messageDiv = document.getElementById("message");
  messageDiv.textContent = message;
  messageDiv.className = `message ${type}`;
  messageDiv.classList.remove("hidden");

  setTimeout(() => {
    messageDiv.classList.add("hidden");
  }, 5000);
}
