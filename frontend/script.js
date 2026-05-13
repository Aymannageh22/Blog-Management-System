// ===== CONFIG =====
const API = "http://127.0.0.1:8000";
const sunIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
const moonIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
let token = localStorage.getItem("blog_token") || "";
let currentPage = 1;
const LIMIT = 5;
let currentPostId = null;
let userRole = localStorage.getItem("blog_role") || "";
let userName = localStorage.getItem("blog_username") || "";

// ===== INIT =====
let allPosts = []; // For local search filtering
document.addEventListener("DOMContentLoaded", () => {
    updateNavbar();
    if (token) {
        fetchUserRole().then(() => {
            showView("feed");
        });
    } else {
        showView("auth");
    }
    
    // Check saved theme
    if (localStorage.getItem("blog_theme") === "light") {
        document.documentElement.classList.add("light-theme");
        document.getElementById("theme-toggle").innerHTML = sunIcon;
    } else {
        document.getElementById("theme-toggle").innerHTML = moonIcon;
    }
});

// ===== FETCH USER ROLE FROM GET /profile =====
async function fetchUserRole() {
    try {
        const res = await fetch(`${API}/profile`, { headers: authHeaders() });
        if (res.ok) {
            const data = await res.json();
            userRole = data.role || "";
            userName = data.username || "";
            localStorage.setItem("blog_role", userRole);
            localStorage.setItem("blog_username", userName);
        } else if (res.status === 401) {
            token = "";
            userRole = "";
            userName = "";
            localStorage.removeItem("blog_token");
            localStorage.removeItem("blog_role");
            localStorage.removeItem("blog_username");
        }
    } catch (err) {
        // Backend offline — keep cached role
    }
    updateNavbar();
}

// ===== VIEW MANAGEMENT =====
function showView(view) {
    // If not logged in, only allow auth view
    if (!token && view !== "auth") {
        view = "auth";
    }

    // Block non-admin from dashboard
    if (view === "dashboard" && userRole !== "admin") {
        showToast("Dashboard is for admins only", "error");
        view = "feed";
    }

    document.querySelectorAll(".view").forEach(v => v.classList.add("hidden"));
    const el = document.getElementById(view + "-view");
    if (el) el.classList.remove("hidden");

    if (view === "dashboard") loadDashboard();
    if (view === "feed") loadPosts();
    if (view === "profile" && token) loadProfile();
    if (view === "create") {
        if (!document.getElementById("edit-post-id").value) {
            document.getElementById("post-form").reset();
            document.getElementById("create-title").textContent = "✍️ Create New Post";
            document.getElementById("post-submit-btn").querySelector(".btn-text").textContent = "Publish Post";
        }
    }
}

function openCreatePost() {
    document.getElementById("edit-post-id").value = "";
    document.getElementById("post-form").reset();
    document.getElementById("create-title").textContent = "✍️ Create New Post";
    document.getElementById("post-submit-btn").querySelector(".btn-text").textContent = "Publish Post";
    showView("create");
}

// ===== NAVBAR (Role-Based) =====
// Admin: Dashboard + Posts + New Post + Profile + Sign Out
// Author: Posts + New Post + Profile + Sign Out
// Reader: Posts + Profile + Sign Out (no New Post)
// Guest: Sign In + Sign Up only (no posts, no nothing)
function updateNavbar() {
    const loggedIn = !!token;
    const isAdmin = userRole === "admin";
    const isAuthor = userRole === "author";
    const canCreate = isAdmin || isAuthor;

    toggle("nav-dashboard-btn", loggedIn && isAdmin);
    toggle("nav-home-btn", loggedIn);
    toggle("nav-create-btn", loggedIn && canCreate);
    toggle("nav-profile-btn", loggedIn);
    toggle("nav-logout-btn", loggedIn);
    toggle("nav-login-btn", !loggedIn);
    toggle("nav-signup-btn", !loggedIn);
}

function toggle(id, show) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle("hidden", !show);
}

// ===== AUTH TABS =====
function switchAuthTab(tab) {
    document.getElementById("login-tab").classList.toggle("active", tab === "login");
    document.getElementById("register-tab").classList.toggle("active", tab === "register");
    document.getElementById("login-form").classList.toggle("hidden", tab !== "login");
    document.getElementById("register-form").classList.toggle("hidden", tab !== "register");
}

// ===== TOAST =====
function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ======================================================
// ===== DASHBOARD: GET / + GET /metrics (ADMIN ONLY) =====
// ======================================================
async function loadDashboard() {
    if (userRole !== "admin") return;

    try {
        const res = await fetch(`${API}/`);
        const data = await res.json();
        document.getElementById("backend-status").textContent = data.message || "Online";
        document.getElementById("backend-status").style.color = "#4ade80";
        document.getElementById("raw-home").textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        document.getElementById("backend-status").textContent = "Offline";
        document.getElementById("backend-status").style.color = "#f87171";
        document.getElementById("raw-home").textContent = "Error: " + err.message;
    }

    try {
        const res = await fetch(`${API}/metrics`);
        const data = await res.json();
        document.getElementById("metric-requests").textContent = data.request_count ?? "—";
        document.getElementById("metric-errors").textContent = data.error_count ?? "—";
        document.getElementById("metric-errors").style.color = data.error_count > 0 ? "#f87171" : "#4ade80";
        const avgTime = data.average_response_time;
        document.getElementById("metric-avg-time").textContent = avgTime !== undefined ? avgTime.toFixed(4) + "s" : "—";
        document.getElementById("metric-health").textContent = (data.system_status || "—").toUpperCase();
        document.getElementById("metric-health").style.color = data.system_status === "healthy" ? "#4ade80" : "#fbbf24";
        document.getElementById("raw-metrics").textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        document.getElementById("raw-metrics").textContent = "Error: " + err.message;
    }

    try {
        const res = await fetch(`${API}/posts?page=1&limit=100`);
        const posts = await res.json();
        document.getElementById("metric-posts-count").textContent = Array.isArray(posts) ? posts.length : "—";
    } catch {
        document.getElementById("metric-posts-count").textContent = "—";
    }
}

// ======================================================
// ===== AUTH: POST /register =====
// ======================================================
async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById("register-submit-btn");
    setLoading(btn, true);
    try {
        const res = await fetch(`${API}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: val("register-username"),
                email: val("register-email"),
                password: val("register-password"),
                role: val("register-role")
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Registration failed");
        showToast("Account created! Please sign in.");
        switchAuthTab("login");
        document.getElementById("register-form").reset();
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        setLoading(btn, false);
    }
}

// ======================================================
// ===== AUTH: POST /login =====
// ======================================================
async function handleLogin(e) {
    e.preventDefault();
    const btn = document.getElementById("login-submit-btn");
    setLoading(btn, true);
    try {
        const form = new URLSearchParams();
        form.append("username", val("login-email"));
        form.append("password", val("login-password"));
        const res = await fetch(`${API}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: form
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Login failed");
        token = data.access_token;
        localStorage.setItem("blog_token", token);

        // Fetch role after login
        await fetchUserRole();
        showToast(`Welcome back, ${userName || "user"}! 🎉`);

        // Admin goes to dashboard, others go to feed
        if (userRole === "admin") {
            showView("dashboard");
        } else {
            showView("feed");
        }
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        setLoading(btn, false);
    }
}

// ===== LOGOUT =====
function logout() {
    token = "";
    userRole = "";
    userName = "";
    localStorage.removeItem("blog_token");
    localStorage.removeItem("blog_role");
    localStorage.removeItem("blog_username");
    updateNavbar();
    showToast("Signed out successfully");
    showView("feed");
}

// ======================================================
// ===== PROFILE: GET /profile (ALL AUTHENTICATED USERS) =====
// ======================================================
async function loadProfile() {
    try {
        const res = await fetch(`${API}/profile`, { headers: authHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to load profile");
        const email = data.user_data?.sub || "—";
        document.getElementById("profile-email").textContent = email;
        document.getElementById("profile-name").textContent = data.username || email.split("@")[0];
        
        const avatarEl = document.getElementById("profile-avatar");
        if (data.profile_image) {
            avatarEl.style.backgroundImage = `url(${API}${data.profile_image})`;
            avatarEl.textContent = "";
        } else {
            avatarEl.style.backgroundImage = "";
            avatarEl.textContent = (data.username || email).charAt(0).toUpperCase();
        }

        // Show role badge with color
        const roleBadge = document.getElementById("profile-badge");
        const role = (data.role || "user").toUpperCase();
        roleBadge.textContent = role;
        if (data.role === "admin") {
            roleBadge.style.background = "rgba(239, 68, 68, 0.15)";
            roleBadge.style.color = "#f87171";
        } else if (data.role === "author") {
            roleBadge.style.background = "rgba(99, 102, 241, 0.25)";
            roleBadge.style.color = "#818cf8";
        } else {
            roleBadge.style.background = "rgba(34, 197, 94, 0.15)";
            roleBadge.style.color = "#4ade80";
        }

        // Fetch and show user's posts
        if (!allPosts.length) {
            // If allPosts is empty, fetch them just in case (e.g. refresh on profile page)
            const postsRes = await fetch(`${API}/posts?page=1&limit=100`);
            if (postsRes.ok) {
                allPosts = await postsRes.json();
            }
        }
        
        const myPosts = allPosts.filter(p => p.author === (data.username || email.split("@")[0]));
        renderProfilePosts(myPosts);

    } catch (err) {
        showToast(err.message, "error");
    }
}

function renderProfilePosts(posts) {
    const grid = document.getElementById("profile-posts-grid");
    const empty = document.getElementById("profile-posts-empty");
    grid.innerHTML = "";
    
    if (!posts || !posts.length) {
        empty.classList.remove("hidden");
        return;
    }
    
    empty.classList.add("hidden");
    posts.forEach((post, i) => {
        const card = document.createElement("div");
        card.className = "post-card glass-card";
        card.style.animationDelay = `${i * 0.05}s`;
        const timeStr = post.created_at ? `<span title="${post.created_at}">⏳ ${timeAgo(post.created_at)}</span>` : "";
        card.innerHTML = `
            <div class="post-card-header">
                <div>
                    <div class="post-card-title">${esc(post.title)}</div>
                    <div class="post-card-meta">
                        ${timeStr}
                        <span class="post-card-comments">💬 ${post.comments ? post.comments.length : 0} comments</span>
                    </div>
                </div>
            </div>
            <p class="post-card-content">${esc(post.content)}</p>
        `;
        card.addEventListener("click", () => viewPost(post.id));
        grid.appendChild(card);
    });
}

// ======================================================
// ===== PROFILE: UPLOAD AVATAR =====
// ======================================================
async function handleAvatarUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const loader = document.getElementById("avatar-loader");
    loader.classList.remove("hidden");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`${API}/upload-profile-image`, {
            method: "POST",
            headers: authHeaders(), // Don't set Content-Type, fetch will set it with boundary for FormData
            body: formData
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to upload image");

        // Update UI immediately
        const avatarEl = document.getElementById("profile-avatar");
        avatarEl.style.backgroundImage = `url(${API}${data.profile_image})`;
        avatarEl.textContent = "";
        
        showToast("Profile image updated successfully! 🎉");
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        loader.classList.add("hidden");
        // Reset input
        event.target.value = "";
    }
}

// ======================================================
// ===== POSTS: GET /posts (with pagination) =====
// ======================================================
async function loadPosts() {
    const grid = document.getElementById("posts-grid");
    const loading = document.getElementById("posts-loading");
    const empty = document.getElementById("posts-empty");
    grid.innerHTML = "";
    loading.classList.remove("hidden");
    empty.classList.add("hidden");
    try {
        const res = await fetch(`${API}/posts?page=${currentPage}&limit=${LIMIT}`);
        const posts = await res.json();
        allPosts = posts; // Cache for search
        renderPostsGrid(posts);
        
        document.getElementById("page-info").textContent = `Page ${currentPage}`;
        document.getElementById("prev-page-btn").disabled = currentPage <= 1;
        document.getElementById("next-page-btn").disabled = posts.length < LIMIT;
    } catch (err) {
        loading.classList.add("hidden");
        showToast("Failed to load posts", "error");
    }
}

function renderPostsGrid(posts) {
    const grid = document.getElementById("posts-grid");
    const empty = document.getElementById("posts-empty");
    grid.innerHTML = "";
    
    if (!posts || !posts.length) {
        empty.classList.remove("hidden");
        return;
    }
    
    empty.classList.add("hidden");
    posts.forEach((post, i) => {
        const card = document.createElement("div");
        card.className = "post-card glass-card";
        card.style.animationDelay = `${i * 0.05}s`;
        const timeStr = post.created_at ? `<span title="${post.created_at}">⏳ ${timeAgo(post.created_at)}</span>` : "";
        card.innerHTML = `
            <div class="post-card-header">
                <div>
                    <div class="post-card-title">${esc(post.title)}</div>
                    <div class="post-card-meta">
                        <span class="post-card-author">✦ ${esc(post.author)}</span>
                        ${timeStr}
                        <span class="post-card-comments">💬 ${post.comments ? post.comments.length : 0} comments</span>
                    </div>
                </div>
            </div>
            <p class="post-card-content">${esc(post.content)}</p>
        `;
        card.addEventListener("click", () => viewPost(post.id));
        grid.appendChild(card);
    });
}

// ===== SEARCH POSTS =====
function handleSearch() {
    const query = val("search-input").toLowerCase();
    if (!query) {
        renderPostsGrid(allPosts);
        return;
    }
    const filtered = allPosts.filter(p => p.title.toLowerCase().includes(query) || p.content.toLowerCase().includes(query));
    renderPostsGrid(filtered);
}

function changePage(delta) {
    currentPage += delta;
    if (currentPage < 1) currentPage = 1;
    loadPosts();
}

// ======================================================
// ===== POST: GET /posts/{post_id} =====
// ======================================================
async function viewPost(postId) {
    currentPostId = postId;
    showView("post");
    const detail = document.getElementById("post-detail");
    detail.innerHTML = '<div class="loading-state"><div class="spinner"></div></div>';
    try {
        const res = await fetch(`${API}/posts/${postId}`);
        const post = await res.json();
        if (!res.ok) throw new Error(post.detail || "Post not found");

        // Role-based actions:
        // Admin: can edit/delete ANY post
        // Author: can edit/delete ONLY their own posts
        // Reader: no edit/delete buttons
        let actionsHTML = "";
        const isAdmin = userRole === "admin";
        const isOwner = token && userName === post.author;

        if (isAdmin || isOwner) {
            actionsHTML = `
            <div class="post-detail-actions">
                <button class="btn btn-outline btn-sm" id="edit-post-btn-${post.id}" onclick="event.stopPropagation(); editPost(${post.id})">✏️ Edit</button>
                <button class="btn btn-danger btn-sm" id="delete-post-btn-${post.id}" onclick="event.stopPropagation(); deletePost(${post.id})">🗑️ Delete</button>
            </div>`;
        }
        
        const timeStr = post.created_at ? `<span style="margin-left: 10px; color: var(--text-muted); font-size: 0.85rem;" title="${post.created_at}">⏳ ${timeAgo(post.created_at)}</span>` : "";

        detail.innerHTML = `
            <h1 class="post-detail-title">${esc(post.title)}</h1>
            <span class="post-detail-author">By ${esc(post.author)}</span>${timeStr}
            <div class="post-detail-body">${esc(post.content)}</div>
            ${actionsHTML}
        `;
        detail.dataset.title = post.title;
        detail.dataset.content = post.content;

        // Comments: all logged-in users can comment (including readers)
        toggle("comment-form", !!token);
        renderComments(post.comments || [], post.author);
    } catch (err) {
        detail.innerHTML = `<p style="color:var(--danger)">${err.message}</p>`;
    }
}

// ======================================================
// ===== COMMENTS: Render with Role-Based Actions =====
// ======================================================
function renderComments(comments, postAuthor) {
    const list = document.getElementById("comments-list");
    if (!comments.length) {
        list.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:20px">No comments yet. Be the first!</p>';
        return;
    }
    const isAdmin = userRole === "admin";

    list.innerHTML = comments.map(c => {
        const safeContent = esc(c.content);
        // Admin: edit/delete any comment
        // Comment owner: edit/delete own comment
        // Others: only reply
        const isCommentOwner = userName === c.user;
        const canModify = isAdmin || isCommentOwner;

        return `
        <div class="comment-item" id="comment-item-${c.id}">
            <div class="comment-user">@${esc(c.user)}</div>
            <div class="comment-text">${safeContent}</div>
            ${token ? `
            <div class="comment-actions">
                <button class="comment-action-btn" id="reply-btn-${c.id}" onclick="openReplyModal(${c.id})">↩ Reply</button>
                ${canModify ? `
                <button class="comment-action-btn" id="edit-comment-btn-${c.id}" onclick="openEditCommentModal(${c.id}, \`${safeContent.replace(/`/g, '')}\`)">✏️ Edit</button>
                <button class="comment-action-btn danger" id="delete-comment-btn-${c.id}" onclick="deleteComment(${c.id})">🗑️ Delete</button>
                ` : ""}
            </div>` : ""}
            ${c.replies && c.replies.length ? `
            <div class="replies-list">
                ${c.replies.map(r => `
                    <div class="reply-item" id="reply-item-${r.id}">
                        <div class="comment-user">@${esc(r.user)}</div>
                        <div class="comment-text">${esc(r.content)}</div>
                    </div>
                `).join("")}
            </div>` : ""}
        </div>`;
    }).join("");
}

// ======================================================
// ===== COMMENT: POST /posts/{post_id}/comments =====
// ======================================================
async function handleCommentSubmit(e) {
    e.preventDefault();
    const content = val("comment-input");
    if (!content) return;
    try {
        const res = await fetch(`${API}/posts/${currentPostId}/comments`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders() },
            body: JSON.stringify({ content })
        });
        if (!res.ok) { const d = await res.json(); throw new Error(d.detail || "Failed"); }
        showToast("Comment added!");
        document.getElementById("comment-input").value = "";
        viewPost(currentPostId);
    } catch (err) { showToast(err.message, "error"); }
}

// ======================================================
// ===== COMMENT: PUT /comments/{comment_id} =====
// ======================================================
function openEditCommentModal(commentId, content) {
    document.getElementById("edit-comment-id").value = commentId;
    document.getElementById("edit-comment-content").value = content;
    document.getElementById("edit-comment-modal").classList.remove("hidden");
}
function closeEditCommentModal() {
    document.getElementById("edit-comment-modal").classList.add("hidden");
}
async function handleEditComment(e) {
    e.preventDefault();
    const id = val("edit-comment-id");
    const content = val("edit-comment-content");
    try {
        const res = await fetch(`${API}/comments/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", ...authHeaders() },
            body: JSON.stringify({ content })
        });
        if (!res.ok) { const d = await res.json(); throw new Error(d.detail || "Failed"); }
        showToast("Comment updated!");
        closeEditCommentModal();
        viewPost(currentPostId);
    } catch (err) { showToast(err.message, "error"); }
}

// ======================================================
// ===== COMMENT: DELETE /comments/{comment_id} =====
// ======================================================
async function deleteComment(commentId) {
    if (!confirm("Delete this comment?")) return;
    try {
        const res = await fetch(`${API}/comments/${commentId}`, {
            method: "DELETE", headers: authHeaders()
        });
        if (!res.ok) { const d = await res.json(); throw new Error(d.detail || "Failed"); }
        showToast("Comment deleted!");
        viewPost(currentPostId);
    } catch (err) { showToast(err.message, "error"); }
}

// ======================================================
// ===== COMMENT: POST /comments/{comment_id}/reply =====
// ======================================================
function openReplyModal(commentId) {
    document.getElementById("reply-comment-id").value = commentId;
    document.getElementById("reply-content").value = "";
    document.getElementById("reply-modal").classList.remove("hidden");
}
function closeReplyModal() {
    document.getElementById("reply-modal").classList.add("hidden");
}
async function handleReply(e) {
    e.preventDefault();
    const id = val("reply-comment-id");
    const content = val("reply-content");
    try {
        const res = await fetch(`${API}/comments/${id}/reply`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders() },
            body: JSON.stringify({ content })
        });
        if (!res.ok) { const d = await res.json(); throw new Error(d.detail || "Failed"); }
        showToast("Reply added!");
        closeReplyModal();
        viewPost(currentPostId);
    } catch (err) { showToast(err.message, "error"); }
}

// ======================================================
// ===== POST: POST /posts + PUT /posts/{post_id} =====
// ======================================================
function editPost(id) {
    const detail = document.getElementById("post-detail");
    const title = detail.dataset.title || "";
    const content = detail.dataset.content || "";
    document.getElementById("edit-post-id").value = id;
    document.getElementById("post-title-input").value = title;
    document.getElementById("post-content-input").value = content;
    document.getElementById("create-title").textContent = "✏️ Edit Post";
    document.getElementById("post-submit-btn").querySelector(".btn-text").textContent = "Update Post";
    showView("create");
}

async function handlePostSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById("post-submit-btn");
    setLoading(btn, true);
    const editId = val("edit-post-id");
    const payload = { title: val("post-title-input"), content: val("post-content-input") };
    try {
        const url = editId ? `${API}/posts/${editId}` : `${API}/posts`;
        const method = editId ? "PUT" : "POST";
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json", ...authHeaders() },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed");
        showToast(editId ? "Post updated!" : "Post published! 🚀");
        document.getElementById("post-form").reset();
        document.getElementById("edit-post-id").value = "";
        showView("feed");
    } catch (err) { showToast(err.message, "error"); }
    finally { setLoading(btn, false); }
}

// ======================================================
// ===== POST: DELETE /posts/{post_id} =====
// ======================================================
async function deletePost(postId) {
    if (!confirm("Delete this post? This action cannot be undone.")) return;
    try {
        const res = await fetch(`${API}/posts/${postId}`, {
            method: "DELETE", headers: authHeaders()
        });
        if (!res.ok) { const d = await res.json(); throw new Error(d.detail || "Failed"); }
        showToast("Post deleted!");
        showView("feed");
    } catch (err) { showToast(err.message, "error"); }
}

// ===== HELPERS & THEME =====
function toggleTheme() {
    const isLight = document.documentElement.classList.toggle("light-theme");
    localStorage.setItem("blog_theme", isLight ? "light" : "dark");
    document.getElementById("theme-toggle").innerHTML = isLight ? sunIcon : moonIcon;
}

function val(id) { return document.getElementById(id).value.trim(); }
function esc(str) {
    if (!str) return "";
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
}
function authHeaders() { return token ? { "Authorization": `Bearer ${token}` } : {}; }
function setLoading(btn, loading) {
    const text = btn.querySelector(".btn-text");
    const loader = btn.querySelector(".btn-loader");
    if (text) text.classList.toggle("hidden", loading);
    if (loader) loader.classList.toggle("hidden", !loading);
    btn.disabled = loading;
}
function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " years ago";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " months ago";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " days ago";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " hours ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + " minutes ago";
    return "just now";
}