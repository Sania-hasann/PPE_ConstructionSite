document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const toggleButton = document.querySelector(".toggle-btn");

    // Automatically collapse sidebar on small screens
    function checkScreenSize() {
        if (window.innerWidth <= 768) {
            sidebar.classList.add("closed");
        } else {
            sidebar.classList.remove("closed");
        }
    }

    // Run on load
    checkScreenSize();

    // Toggle sidebar when button is clicked
    toggleButton.addEventListener("click", function () {
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle("expanded");
        } else {
            sidebar.classList.toggle("closed");
        }
    });

    // Ensure sidebar adjusts when window resizes
    window.addEventListener("resize", checkScreenSize);
});


/* UPLOAD PAGE */
document.addEventListener("DOMContentLoaded", function () {
    const dropArea = document.getElementById("dropArea");
    const fileInput = document.getElementById("fileInput");
    const browseButton = document.getElementById("browseButton");
    const processingContainer = document.getElementById("processingContainer");
    const progressBar = document.querySelector(".progress-bar");
    const videoContainer = document.getElementById("videoContainer");
    const videoElement = document.querySelector("video");

    browseButton.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", function (event) {
        processFile(event.target.files[0]);
    });

    dropArea.addEventListener("dragover", (event) => {
        event.preventDefault();
        dropArea.style.backgroundColor = "#f0f0ff";
    });

    dropArea.addEventListener("dragleave", () => {
        dropArea.style.backgroundColor = "white";
    });

    dropArea.addEventListener("drop", (event) => {
        event.preventDefault();
        dropArea.style.backgroundColor = "white";
        const file = event.dataTransfer.files[0];
        processFile(file);
    });

    function processFile(file) {
        if (file && file.type.startsWith("video/")) {
            processingContainer.style.display = "block";  // Ensure it's visible
            const progressElement = document.querySelector(".progress"); // Get progress div
            progressElement.style.width = "0%";
            progressElement.innerText = "0%";
        
            uploadFile(file);
            trackProgress();  // Start real-time tracking
        } else {
            alert("Please upload a valid video file.");
        }
    }      
    
    function uploadFile(file) {
        const formData = new FormData();
        formData.append("file", file);
    
        // Display only the uploaded video
        const uploadedFileURL = URL.createObjectURL(file);
        videoElement.src = uploadedFileURL;
        videoContainer.style.display = "block";
    
        fetch("/video", {
            method: "POST",
            body: formData,
        })
        .then(response => response.blob())
        .then(blob => {
            console.log("Processing completed, but the processed video will not be displayed.");
            // Do not update videoElement.src here
        })
        .catch(error => {
            console.error("Upload failed:", error);
            alert("Failed to process video.");
        });
    }        

    function trackProgress() {
        const eventSource = new EventSource("/stream");
        const progressElement = document.querySelector(".progress-bar");
    
        eventSource.onmessage = function (event) {
            let percentage = parseInt(event.data);
            console.log("Progress:", percentage);
    
            progressElement.style.width = percentage + "%";
            progressElement.innerText = percentage + "%";
    
            if (percentage >= 100) {
                eventSource.close();  // Stop tracking once done
                progressElement.innerText = "Processing Complete!";
            }
        };
    }       
    
    // Function to display video
    function showVideo(file) {
        const fileURL = URL.createObjectURL(file);
        videoElement.src = fileURL;
        videoContainer.style.display = "block";
    }
});

// document.addEventListener("DOMContentLoaded", function () {
//     const dropArea = document.getElementById("dropArea");
//     const fileInput = document.getElementById("fileInput");
//     const browseButton = document.getElementById("browseButton");
//     const processingContainer = document.getElementById("processingContainer");
//     const progressBar = document.querySelector(".progress");
//     const videoContainer = document.getElementById("videoContainer");
//     const videoElement = document.querySelector("video");

//     browseButton.addEventListener("click", () => {
//         fileInput.click();
//     });

//     fileInput.addEventListener("change", function (event) {
//         processFile(event.target.files[0]);
//     });

//     dropArea.addEventListener("dragover", (event) => {
//         event.preventDefault();
//         dropArea.style.backgroundColor = "#f0f0ff";
//     });

//     dropArea.addEventListener("dragleave", () => {
//         dropArea.style.backgroundColor = "white";
//     });

//     dropArea.addEventListener("drop", (event) => {
//         event.preventDefault();
//         dropArea.style.backgroundColor = "white";
//         const file = event.dataTransfer.files[0];
//         processFile(file);
//     });

//     function processFile(file) {
//         if (file && file.type.startsWith("video/")) {
//             processingContainer.style.display = "block";
//             progressBar.style.width = "0%";
    
//             uploadFile(file);
//             trackProgress();  // Start real-time tracking
//         } else {
//             alert("Please upload a valid video file.");
//         }
//     }

//     function uploadFile(file) {
//         const formData = new FormData();
//         formData.append("file", file);

//         fetch("/video", {
//             method: "POST",
//             body: formData,
//         })
//         .then(response => {
//             if (!response.ok) {
//                 throw new Error("Error processing video.");
//             }
//             return response.blob();
//         })
//         .then(blob => {
//             const fileURL = URL.createObjectURL(blob);
//             videoElement.src = fileURL;
//             videoContainer.style.display = "block";
//         })
//         .catch(error => {
//             console.error("Upload failed:", error);
//             alert("Failed to process video.");
//         });
//     }
//     // Function to display video
//     function showVideo(file) {
//         const fileURL = URL.createObjectURL(file);
//         videoElement.src = fileURL;
//         videoContainer.style.display = "block";
//     }
// });

/* NOTIFICATIONS PAGE */
document.addEventListener("DOMContentLoaded", function () {
    const notifications = [
        { id: 1, text: "New project assigned!", read: false },
        { id: 2, text: "Your report has been approved.", read: true },
        { id: 3, text: "Meeting scheduled at 3 PM.", read: false },
        { id: 4, text: "Reminder: Submit your feedback.", read: true },
        { id: 5, text: "Server maintenance scheduled.", read: false },
        { id: 6, text: "New comment on your post.", read: false },
        { id: 7, text: "New project assigned!", read: false },
        { id: 8, text: "Your report has been approved.", read: true },
        { id: 9, text: "Meeting scheduled at 3 PM.", read: false },
        { id: 10, text: "Reminder: Submit your feedback.", read: true },
        { id: 11, text: "Server maintenance scheduled.", read: false },
        { id: 12, text: "New comment on your post.", read: false },
    ];

    const notificationContainer = document.getElementById("notifications-list");
    const viewAllButton = document.getElementById("view-all-btn");
    let expanded = false; // Flag to track whether all notifications are displayed

    function renderNotifications() {
        notificationContainer.innerHTML = "";
        const visibleNotifications = expanded ? notifications : notifications.slice(0, 5);

        visibleNotifications.forEach(notification => {
            const notificationElement = document.createElement("div");
            notificationElement.classList.add("notification-item");
            if (!notification.read) {
                notificationElement.classList.add("unread");
            }
            notificationElement.textContent = notification.text;
            notificationContainer.appendChild(notificationElement);
        });

        viewAllButton.textContent = expanded ? "Show Less" : "View All Notifications";
        viewAllButton.style.display = notifications.length > 5 ? "block" : "none";

    }

    // Event Listener for View All Notifications Button
    viewAllButton.addEventListener("click", function () {
        expanded = !expanded;
        document.querySelector(".notifications-container").classList.toggle("expanded", expanded);
        renderNotifications();
    });

    // Event Listeners for Large Screen Buttons
    document.getElementById("mark-read")?.addEventListener("click", function () {
        notifications.forEach(notification => notification.read = true);
        renderNotifications();
    });

    document.getElementById("clear-all")?.addEventListener("click", function () {
        notifications.length = 0;
        renderNotifications();
    });

    // Event Listeners for Dropdown Buttons (Small Screens)
    document.getElementById("dropdown-mark-read")?.addEventListener("click", function () {
        notifications.forEach(notification => notification.read = true);
        renderNotifications();
        toggleMenu(); // Close dropdown after action
    });

    document.getElementById("dropdown-clear-all")?.addEventListener("click", function () {
        notifications.length = 0;
        renderNotifications();
        toggleMenu(); // Close dropdown after action
    });

    renderNotifications();
});

// Toggle dropdown menu
function toggleMenu() {
    const dropdown = document.getElementById("dropdownMenu");
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

// Hide dropdown when clicking outside
document.addEventListener("click", function (event) {
    const menu = document.getElementById("dropdownMenu");
    const icon = document.querySelector(".menu-icon");

    if (menu && !menu.contains(event.target) && icon && !icon.contains(event.target)) {
        menu.style.display = "none";
    }
});

/* document.addEventListener("DOMContentLoaded", function() {
    loadNotifications();
});

function loadNotifications() {
    let newNotifications = [
        { name: "Video 01", message: "Notifications/preprocessings", time: "1 hr ago" },
        { name: "Video 02", message: "Notifications/preprocessings", time: "2 hr ago" }
    ];
    let previousNotifications = [
        { name: "Video 03", message: "Notifications/preprocessings", time: "1 day ago" },
        { name: "Video 04", message: "Notifications/preprocessings", time: "3 days ago" }
    ];

    displayNotifications("new-notifications", newNotifications);
    displayNotifications("previous-notifications", previousNotifications);
    document.getElementById("new-count").textContent = newNotifications.length;
}

function displayNotifications(containerId, notifications) {
    let container = document.getElementById(containerId);
    container.innerHTML = "";
    notifications.slice(0, 5).forEach(notif => {
        let div = document.createElement("div");
        div.className = "notification-item";
        div.innerHTML = `<strong>${notif.name}</strong>: ${notif.message} <span style="float: right;">${notif.time}</span>`;
        container.appendChild(div);
    });
}

function switchTab(tab) {
    document.querySelector(".tab.active").classList.remove("active");
    document.querySelector(`.tab[onclick="switchTab('${tab}')"]`).classList.add("active");

    document.getElementById("new-notifications").classList.toggle("hidden", tab !== "new");
    document.getElementById("previous-notifications").classList.toggle("hidden", tab !== "previous");
}

function markAllRead() {
    alert("All notifications marked as read.");
}

function clearAll() {
    alert("All notifications cleared.");
} */
