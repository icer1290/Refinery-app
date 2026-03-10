const DEEPSEARCH_MAX_ITERATIONS = 10;
const DEEPSEARCH_TIMEOUT_MS = 5 * 60 * 1000;

const state = {
  view: "home",
  route: {
    type: "list",
    articleId: null,
  },
  authMode: "login",
  session: loadJSON("technews.session", null),
  apiBaseUrl: normalizeBaseUrl(localStorage.getItem("technews.apiBaseUrl")) || "",
  articlesById: new Map(),
  homeArticleIds: [],
  favoriteArticleIds: [],
  archiveDates: [],
  nextArchiveDateIndex: 0,
  preferences: {
    id: null,
    preferredCategories: [],
    notificationEnabled: false,
  },
  scrollPositions: {
    home: 0,
    favorites: 0,
  },
  homeErrorMessage: "",
  favoritesErrorMessage: "",
  profileErrorMessage: "",
  deepSearchErrorMessage: "",
  isLoadingHome: false,
  isLoadingMore: false,
  isLoadingFavorites: false,
  isSavingPreferences: false,
  isSubmittingAuth: false,
  loadingDeepSearchIds: new Set(),
};

const els = {
  navButtons: [...document.querySelectorAll(".nav-button")],
  viewTitle: document.getElementById("view-title"),
  viewSubtitle: document.getElementById("view-subtitle"),
  refreshButton: document.getElementById("refresh-button"),
  backButton: document.getElementById("back-button"),
  contentRoot: document.getElementById("content-root"),
  scrollSentinel: document.getElementById("scroll-sentinel"),
  openAuthButton: document.getElementById("open-auth-button"),
  closeAuthButton: document.getElementById("close-auth-button"),
  logoutButton: document.getElementById("logout-button"),
  sessionSummary: document.getElementById("session-summary"),
  authModal: document.getElementById("auth-modal"),
  authForm: document.getElementById("auth-form"),
  authError: document.getElementById("auth-error"),
  authSubmitButton: document.getElementById("auth-submit-button"),
  authEmail: document.getElementById("auth-email"),
  authPassword: document.getElementById("auth-password"),
  authNickname: document.getElementById("auth-nickname"),
  nicknameField: document.getElementById("nickname-field"),
  authModeButtons: [...document.querySelectorAll("[data-auth-mode]")],
};

const scrollObserver = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting && state.view === "home" && state.route.type === "list") {
        loadNextArchiveDay();
      }
    }
  },
  { rootMargin: "320px 0px" }
);

bootstrap().catch((error) => {
  console.error(error);
  renderFatal(getErrorMessage(error));
});

async function bootstrap() {
  bindEvents();
  scrollObserver.observe(els.scrollSentinel);
  render();
  await refreshAll();
}

function bindEvents() {
  els.navButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      persistCurrentScroll();
      state.view = button.dataset.view;
      if (button.dataset.view === "home" || button.dataset.view === "favorites") {
        state.route = { type: "list", articleId: null };
      } else {
        state.route = { type: "list", articleId: null };
      }
      if (state.view === "favorites" && state.session?.token) {
        await loadFavorites();
      }
      if (state.view === "profile" && state.session?.token) {
        await loadPreferences();
      }
      render();
      restoreScrollForCurrentRoute();
    });
  });

  els.refreshButton.addEventListener("click", async () => {
    if (state.view === "favorites") {
      await loadFavorites();
    } else if (state.view === "profile") {
      await loadPreferences();
    } else {
      await refreshHome();
    }
    render();
  });

  els.backButton.addEventListener("click", () => {
    state.route = { type: "list", articleId: null };
    render();
    restoreScrollForCurrentRoute();
  });

  els.openAuthButton.addEventListener("click", () => toggleAuthModal(true));
  els.closeAuthButton.addEventListener("click", () => toggleAuthModal(false));
  els.logoutButton.addEventListener("click", handleLogout);
  els.authModal.addEventListener("click", (event) => {
    if (event.target === els.authModal) {
      toggleAuthModal(false);
    }
  });

  els.authModeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.authMode = button.dataset.authMode;
      renderAuthMode();
    });
  });

  els.authForm.addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuth();
  });
}

async function refreshAll() {
  await refreshHome();
  if (state.session?.token) {
    await Promise.all([loadFavorites(), loadPreferences()]);
  } else {
    resetAuthenticatedState();
  }
  render();
}

async function refreshHome() {
  state.isLoadingHome = true;
  state.homeErrorMessage = "";
  state.homeArticleIds = [];
  state.archiveDates = [];
  state.nextArchiveDateIndex = 0;
  render();

  try {
    const todayArticles = await apiRequest("api/news/today", { token: state.session?.token });
    const sortedToday = sortArticles(todayArticles, "today");
    upsertArticles(sortedToday);
    state.homeArticleIds = sortedToday.map((article) => article.id);

    const dates = await apiRequest("api/news/dates");
    const todayKey = new Date().toISOString().slice(0, 10);
    state.archiveDates = dates
      .filter((dateKey) => dateKey !== todayKey)
      .sort((a, b) => new Date(b).getTime() - new Date(a).getTime());
  } catch (error) {
    state.homeErrorMessage = getErrorMessage(error);
  } finally {
    state.isLoadingHome = false;
    render();
  }
}

async function loadNextArchiveDay() {
  if (state.isLoadingMore || state.nextArchiveDateIndex >= state.archiveDates.length) {
    return;
  }

  state.isLoadingMore = true;
  render();
  const dateKey = state.archiveDates[state.nextArchiveDateIndex];
  state.nextArchiveDateIndex += 1;

  try {
    const params = new URLSearchParams({ startDate: dateKey, endDate: dateKey });
    const archiveArticles = await apiRequest(`api/news/archive?${params.toString()}`, { token: state.session?.token });
    const sortedArchive = sortArticles(archiveArticles, "archive");
    upsertArticles(sortedArchive);
    for (const article of sortedArchive) {
      if (!state.homeArticleIds.includes(article.id)) {
        state.homeArticleIds.push(article.id);
      }
    }
  } catch (error) {
    state.homeErrorMessage = getErrorMessage(error);
  } finally {
    state.isLoadingMore = false;
    render();
  }
}

async function loadFavorites() {
  if (!state.session?.token) {
    resetAuthenticatedState();
    return;
  }

  state.isLoadingFavorites = true;
  state.favoritesErrorMessage = "";
  render();
  try {
    const favorites = await apiRequest("api/user/favorites", { token: state.session.token });
    const sortedFavorites = [...favorites].sort((a, b) => timeValue(b.processedAt) - timeValue(a.processedAt));
    upsertArticles(sortedFavorites);
    state.favoriteArticleIds = sortedFavorites.map((article) => article.id);
    syncFavoriteFlags(new Set(state.favoriteArticleIds));
  } catch (error) {
    state.favoritesErrorMessage = getErrorMessage(error);
  } finally {
    state.isLoadingFavorites = false;
    render();
  }
}

async function loadPreferences() {
  if (!state.session?.token) {
    state.preferences = { id: null, preferredCategories: [], notificationEnabled: false };
    return;
  }

  state.profileErrorMessage = "";
  try {
    state.preferences = await apiRequest("api/user/preferences", { token: state.session.token });
  } catch (error) {
    state.profileErrorMessage = getErrorMessage(error);
  }
}

async function openArticleDetail(articleId) {
  persistCurrentScroll();
  state.route = { type: "detail", articleId };
  render();
  scrollToTopSoon();
  try {
    const article = await apiRequest(`api/news/${articleId}`, { token: state.session?.token });
    upsertArticles([article]);
  } catch (error) {
    state.homeErrorMessage = getErrorMessage(error);
  } finally {
    render();
  }
}

async function toggleFavorite(articleId) {
  if (!state.session?.token) {
    toggleAuthModal(true);
    return;
  }

  const article = state.articlesById.get(articleId);
  if (!article) {
    return;
  }

  const previousValue = Boolean(article.isFavorite);
  article.isFavorite = !previousValue;
  state.articlesById.set(articleId, article);

  if (article.isFavorite) {
    if (!state.favoriteArticleIds.includes(articleId)) {
      state.favoriteArticleIds.unshift(articleId);
    }
  } else {
    state.favoriteArticleIds = state.favoriteArticleIds.filter((id) => id !== articleId);
  }
  render();

  try {
    await apiRequest(`api/news/${articleId}/favorite`, {
      method: article.isFavorite ? "POST" : "DELETE",
      token: state.session.token,
      expectEmpty: true,
    });
  } catch (error) {
    article.isFavorite = previousValue;
    state.articlesById.set(articleId, article);
    if (previousValue) {
      if (!state.favoriteArticleIds.includes(articleId)) {
        state.favoriteArticleIds.unshift(articleId);
      }
    } else {
      state.favoriteArticleIds = state.favoriteArticleIds.filter((id) => id !== articleId);
    }
    alert(getErrorMessage(error));
    render();
  }
}

async function runDeepSearch(articleId) {
  if (!state.session?.token) {
    toggleAuthModal(true);
    return;
  }
  if (state.loadingDeepSearchIds.has(articleId)) {
    return;
  }

  state.loadingDeepSearchIds.add(articleId);
  state.deepSearchErrorMessage = "";
  render();
  try {
    const result = await apiRequest(`api/news/${articleId}/deepsearch?maxIterations=${DEEPSEARCH_MAX_ITERATIONS}`, {
      method: "POST",
      token: state.session.token,
      timeoutMs: DEEPSEARCH_TIMEOUT_MS,
      body: {
        article_id: articleId,
        max_iterations: DEEPSEARCH_MAX_ITERATIONS,
      },
    });

    const article = state.articlesById.get(articleId);
    if (article) {
      article.deepsearchReport = result.final_report;
      article.deepsearchPerformedAt = new Date().toISOString();
      state.articlesById.set(articleId, article);
    }
  } catch (error) {
    state.deepSearchErrorMessage = getErrorMessage(error);
  } finally {
    state.loadingDeepSearchIds.delete(articleId);
    render();
  }
}

async function submitAuth() {
  state.isSubmittingAuth = true;
  els.authError.classList.add("hidden");
  renderAuthMode();

  const payload = {
    email: els.authEmail.value.trim(),
    password: els.authPassword.value,
  };

  if (state.authMode === "register") {
    payload.nickname = els.authNickname.value.trim();
  }

  try {
    const session = await apiRequest(`api/auth/${state.authMode === "login" ? "login" : "register"}`, {
      method: "POST",
      body: payload,
    });
    state.session = session;
    localStorage.setItem("technews.session", JSON.stringify(session));
    toggleAuthModal(false);
    await refreshAll();
  } catch (error) {
    els.authError.textContent = getErrorMessage(error);
    els.authError.classList.remove("hidden");
  } finally {
    state.isSubmittingAuth = false;
    renderAuthMode();
    render();
  }
}

function handleLogout() {
  persistCurrentScroll();
  state.session = null;
  localStorage.removeItem("technews.session");
  resetAuthenticatedState();
  state.view = "home";
  state.route = { type: "list", articleId: null };
  render();
  restoreScrollForCurrentRoute();
}

async function savePreferences(event) {
  event.preventDefault();
  if (!state.session?.token) {
    toggleAuthModal(true);
    return;
  }

  const categoriesText = document.getElementById("categories-input").value;
  const notificationEnabled = document.getElementById("notification-input").checked;
  state.isSavingPreferences = true;
  state.profileErrorMessage = "";
  render();

  try {
    state.preferences = await apiRequest("api/user/preferences", {
      method: "PUT",
      token: state.session.token,
      body: {
        preferredCategories: categoriesText.split(",").map((item) => item.trim()).filter(Boolean),
        notificationEnabled,
      },
    });
  } catch (error) {
    state.profileErrorMessage = getErrorMessage(error);
  } finally {
    state.isSavingPreferences = false;
    render();
  }
}

async function saveApiBaseUrl(event) {
  event.preventDefault();
  const input = document.getElementById("server-url-input");
  state.apiBaseUrl = normalizeBaseUrl(input.value.trim()) || "";
  if (state.apiBaseUrl) {
    localStorage.setItem("technews.apiBaseUrl", state.apiBaseUrl);
  } else {
    localStorage.removeItem("technews.apiBaseUrl");
  }
  await refreshAll();
}

function render() {
  renderChrome();
  renderView();
}

function renderChrome() {
  const titleMap = {
    home: state.route.type === "detail" ? "新闻详情" : "主页",
    favorites: state.route.type === "detail" ? "新闻详情" : "收藏",
    profile: "个人信息",
  };

  const subtitleMap = {
    home: state.route.type === "detail"
      ? "查看新闻摘要、发布时间、收藏状态，以及更深入的分析内容。"
      : "按热度排序展示今日新闻，滚动到底后会继续加载更早的内容。",
    favorites: state.route.type === "detail"
      ? "这是你从收藏列表打开的新闻详情。"
      : "这里会展示你收藏过的新闻，点击卡片可查看详情。",
    profile: "管理账号状态、阅读偏好和服务地址。",
  };

  els.viewTitle.textContent = titleMap[state.view];
  els.viewSubtitle.textContent = subtitleMap[state.view];
  els.backButton.classList.toggle("hidden", !(state.view !== "profile" && state.route.type === "detail"));

  els.navButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === state.view);
  });

  els.sessionSummary.textContent = state.session
    ? `${state.session.nickname || "已登录用户"} · ${state.session.email}`
    : "未登录";
  els.logoutButton.classList.toggle("hidden", !state.session);
  els.scrollSentinel.classList.toggle("hidden", !(state.view === "home" && state.route.type === "list"));
}

function persistCurrentScroll() {
  if (state.route.type === "list" && (state.view === "home" || state.view === "favorites")) {
    state.scrollPositions[state.view] = window.scrollY;
  }
}

function restoreScrollForCurrentRoute() {
  if (state.route.type === "list" && (state.view === "home" || state.view === "favorites")) {
    const target = state.scrollPositions[state.view] || 0;
    requestAnimationFrame(() => window.scrollTo({ top: target, behavior: "auto" }));
    return;
  }

  requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "auto" }));
}

function scrollToTopSoon() {
  requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "auto" }));
}

function renderView() {
  if (state.view === "profile") {
    renderProfileView();
    return;
  }

  if (state.route.type === "detail") {
    renderDetailView();
    return;
  }

  if (state.view === "favorites") {
    renderFavoritesView();
    return;
  }

  renderHomeFeed();
}

function renderHomeFeed() {
  if (state.isLoadingHome && state.homeArticleIds.length === 0) {
    els.contentRoot.innerHTML = renderEmpty("正在加载新闻", "正在为你准备今天的新闻内容。");
    return;
  }

  if (!state.homeArticleIds.length) {
    els.contentRoot.innerHTML = renderEmpty("暂无新闻", state.homeErrorMessage || "暂时没有可展示的新闻，请稍后再试。");
    return;
  }

  els.contentRoot.innerHTML = state.homeArticleIds
    .map((id) => renderFeedCard(state.articlesById.get(id)))
    .join("") + (state.isLoadingMore ? `<div class="empty-state"><p>正在加载更早的新闻...</p></div>` : "");

  bindFeedCardEvents(els.contentRoot);
}

function renderFavoritesView() {
  if (!state.session?.token) {
    els.contentRoot.innerHTML = renderEmpty("请先登录", "登录后即可查看和管理你收藏的新闻。");
    return;
  }

  if (state.isLoadingFavorites && state.favoriteArticleIds.length === 0) {
    els.contentRoot.innerHTML = renderEmpty("正在加载收藏", "稍后会展示你保存过的新闻。");
    return;
  }

  if (!state.favoriteArticleIds.length) {
    els.contentRoot.innerHTML = renderEmpty("还没有收藏", state.favoritesErrorMessage || "点击新闻卡片或详情页中的心形图标即可收藏。");
    return;
  }

  els.contentRoot.innerHTML = state.favoriteArticleIds
    .map((id) => renderFeedCard(state.articlesById.get(id), true))
    .join("");

  bindFeedCardEvents(els.contentRoot, true);
}

function renderDetailView() {
  const article = state.articlesById.get(state.route.articleId);
  if (!article) {
    els.contentRoot.innerHTML = renderEmpty("未找到新闻", "这条新闻可能已被移除或暂时无法访问。");
    return;
  }

  els.contentRoot.innerHTML = `
    <article class="detail-card">
      <div class="detail-header">
        <div>
          <p class="meta-line">新闻详情</p>
          <h3 class="detail-headline">${escapeHtml(article.chineseTitle || article.originalTitle || "未命名新闻")}</h3>
        </div>
        <button class="favorite-icon ${article.isFavorite ? "is-active" : ""}" data-favorite-id="${escapeAttribute(article.id)}" type="button">${article.isFavorite ? "♥" : "♡"}</button>
      </div>

      <p class="detail-summary">${escapeHtml(article.chineseSummary || article.originalDescription || "暂时没有摘要内容。")}</p>

      <div class="detail-meta-grid">
        <section class="detail-meta-card">
          <span class="meta-line">综合评分</span>
          <strong>${escapeHtml(formatScore(article.totalScore))}</strong>
        </section>
        <section class="detail-meta-card">
          <span class="meta-line">发布时间</span>
          <strong>${escapeHtml(formatDate(article.publishedAt))}</strong>
        </section>
        <section class="detail-meta-card">
          <span class="meta-line">来源</span>
          <strong>${escapeHtml(article.sourceName || "未知来源")}</strong>
        </section>
        <section class="detail-meta-card">
          <span class="meta-line">原文链接</span>
          ${article.sourceUrl
            ? `<a class="detail-link" href="${escapeAttribute(article.sourceUrl)}" target="_blank" rel="noreferrer">查看原文</a>`
            : "<strong>暂无链接</strong>"}
        </section>
      </div>

      <section class="deepsearch-card">
        <div class="deepsearch-actions">
          <div>
            <p class="meta-line">深度分析</p>
            <div class="muted">点击按钮生成这条新闻的延伸分析内容。</div>
          </div>
          <button class="primary-button" id="deepsearch-button" type="button">${state.loadingDeepSearchIds.has(article.id) ? "生成中..." : "开始分析"}</button>
        </div>
        ${state.deepSearchErrorMessage ? `<p class="inline-error">${escapeHtml(state.deepSearchErrorMessage)}</p>` : ""}
        <div class="detail-deepsearch">${article.deepsearchReport ? renderMarkdown(article.deepsearchReport) : "<p>当前还没有分析内容，点击按钮即可生成。</p>"}</div>
      </section>
    </article>
  `;

  const favoriteButton = els.contentRoot.querySelector("[data-favorite-id]");
  const deepsearchButton = document.getElementById("deepsearch-button");
  favoriteButton?.addEventListener("click", () => toggleFavorite(article.id));
  deepsearchButton?.addEventListener("click", () => runDeepSearch(article.id));
}

function renderProfileView() {
  if (!state.session?.token) {
    els.contentRoot.innerHTML = `
      <section class="profile-card">
        <p class="meta-line">账号信息</p>
        <h3 class="profile-title">未登录</h3>
        <p class="profile-copy">登录后可以同步收藏、保存阅读偏好，并使用深度分析功能。</p>
        <button id="profile-login-button" class="primary-button" type="button">登录 / 注册</button>
      </section>
      ${renderServerCard()}
    `;
    document.getElementById("profile-login-button")?.addEventListener("click", () => toggleAuthModal(true));
    bindServerForm();
    return;
  }

  els.contentRoot.innerHTML = `
    <section class="profile-card">
      <p class="meta-line">账号信息</p>
      <h3 class="profile-title">${escapeHtml(state.session.nickname || "已登录用户")}</h3>
      <p class="profile-copy">${escapeHtml(state.session.email)}</p>
      <form id="preferences-form">
        <div class="field-grid">
          <label>
            <span>偏好分类</span>
            <textarea id="categories-input" placeholder="例如：AI、大模型、芯片">${escapeHtml(state.preferences.preferredCategories.join(", "))}</textarea>
          </label>
          <label class="toggle-row">
            <span>通知开关</span>
            <input id="notification-input" type="checkbox" ${state.preferences.notificationEnabled ? "checked" : ""}>
          </label>
        </div>
        ${state.profileErrorMessage ? `<p class="form-error">${escapeHtml(state.profileErrorMessage)}</p>` : ""}
        <button class="ghost-button" type="submit">${state.isSavingPreferences ? "保存中..." : "保存偏好"}</button>
      </form>
    </section>
    ${renderServerCard()}
  `;

  document.getElementById("preferences-form")?.addEventListener("submit", savePreferences);
  bindServerForm();
}

function renderServerCard() {
  return `
    <section class="profile-card">
      <p class="meta-line">连接设置</p>
      <h3 class="profile-title">服务地址</h3>
      <p class="profile-copy">默认使用当前站点的服务地址。只有在连接其他服务时才需要修改。</p>
      <form id="server-form">
        <div class="field-grid two">
          <label>
            <span>服务地址</span>
            <input id="server-url-input" type="url" value="${escapeAttribute(state.apiBaseUrl)}" placeholder="http://localhost:8080">
          </label>
          <button class="ghost-button" type="submit">保存</button>
        </div>
      </form>
    </section>
  `;
}

function bindServerForm() {
  document.getElementById("server-form")?.addEventListener("submit", saveApiBaseUrl);
}

function bindFeedCardEvents(scope, fromFavorites = false) {
  scope.querySelectorAll("[data-open-id]").forEach((element) => {
    element.addEventListener("click", () => {
      const articleId = element.getAttribute("data-open-id");
      if (fromFavorites) {
        state.view = "favorites";
      }
      openArticleDetail(articleId);
    });
  });

  scope.querySelectorAll("[data-favorite-id]").forEach((element) => {
    element.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleFavorite(element.getAttribute("data-favorite-id"));
    });
  });
}

function renderFeedCard(article) {
  if (!article) {
    return "";
  }

  return `
    <article class="feed-card">
      <button class="feed-main" data-open-id="${escapeAttribute(article.id)}" type="button">
        <h3 class="feed-title">${escapeHtml(article.displayTitle)}</h3>
        <p class="feed-preview">${escapeHtml(article.displayPreview)}</p>
        <div class="feed-footer">
          <span>${escapeHtml(article.sourceName || "未知来源")}</span>
          <span>${escapeHtml(formatDate(article.processedAt))}</span>
        </div>
      </button>
      <div>
        <div class="score-pill">评分 ${escapeHtml(formatScore(article.totalScore))}</div>
        <button class="favorite-icon ${article.isFavorite ? "is-active" : ""}" data-favorite-id="${escapeAttribute(article.id)}" type="button">${article.isFavorite ? "♥" : "♡"}</button>
      </div>
    </article>
  `;
}

function renderEmpty(title, description) {
  return `
    <div class="empty-state">
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(description)}</p>
    </div>
  `;
}

function renderFatal(message) {
  els.contentRoot.innerHTML = renderEmpty("页面加载失败", message);
}

function renderAuthMode() {
  els.authModeButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.authMode === state.authMode);
  });
  els.nicknameField.classList.toggle("hidden", state.authMode !== "register");
  els.authSubmitButton.textContent = state.isSubmittingAuth
    ? "提交中..."
    : (state.authMode === "login" ? "登录" : "创建账户");
}

function toggleAuthModal(open) {
  els.authModal.classList.toggle("hidden", !open);
  els.authModal.setAttribute("aria-hidden", String(!open));
  if (!open) {
    els.authError.classList.add("hidden");
    els.authForm.reset();
    state.authMode = "login";
    renderAuthMode();
  }
}

async function apiRequest(path, options = {}) {
  const url = buildApiUrl(path);
  const headers = { Accept: "application/json" };
  const controller = options.timeoutMs ? new AbortController() : null;
  const timeoutId = controller
    ? setTimeout(() => controller.abort("REQUEST_TIMEOUT"), options.timeoutMs)
    : null;

  if (options.body) {
    headers["Content-Type"] = "application/json";
  }
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  let response;
  try {
    response = await fetch(url, {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: controller?.signal,
    });
  } catch (error) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    if (controller?.signal.aborted) {
      throw new Error("分析耗时超过五分钟，请稍后重试。");
    }

    throw error;
  }

  if (timeoutId) {
    clearTimeout(timeoutId);
  }

  if (response.status === 401) {
    throw new Error("请先登录后再继续操作。");
  }

  const contentType = response.headers.get("content-type") || "";
  const rawBody = await response.text();

  if (!contentType.includes("application/json")) {
    throw new Error(mapNonJsonError(response.status, rawBody));
  }

  let envelope;
  try {
    envelope = JSON.parse(rawBody);
  } catch {
    throw new Error(mapNonJsonError(response.status, rawBody));
  }

  if (!response.ok || !envelope.success) {
    throw new Error(envelope.message || `Request failed with status ${response.status}`);
  }

  if (options.expectEmpty) {
    return null;
  }

  if (Array.isArray(envelope.data)) {
    return envelope.data.map(normalizePayload);
  }
  return normalizePayload(envelope.data);
}

function mapNonJsonError(status, rawBody) {
  const htmlLike = /^\s*</.test(rawBody || "");

  if (status === 504 || status === 502 || status === 503) {
    return "分析服务暂时不可用，请稍后重试。";
  }

  if (htmlLike) {
    return "分析服务暂时不可用，请稍后重试。";
  }

  if (status >= 400) {
    return `请求失败（${status}），请稍后重试。`;
  }

  return "服务返回了无法识别的数据，请稍后重试。";
}

function normalizePayload(payload) {
  if (!payload || typeof payload !== "object") {
    return payload;
  }

  if ("id" in payload) {
    return {
      ...payload,
      displayTitle: firstNonEmpty(payload.chineseTitle, payload.originalTitle, "未命名新闻"),
      displayPreview: firstNonEmpty(payload.chineseSummary, payload.originalDescription, "暂时没有摘要内容。"),
    };
  }

  return payload;
}

function upsertArticles(articles) {
  for (const article of articles) {
    state.articlesById.set(article.id, {
      ...state.articlesById.get(article.id),
      ...article,
    });
  }
}

function syncFavoriteFlags(favoriteIds) {
  for (const [id, article] of state.articlesById.entries()) {
    article.isFavorite = favoriteIds.has(id);
    state.articlesById.set(id, article);
  }
}

function resetAuthenticatedState() {
  state.favoriteArticleIds = [];
  state.preferences = { id: null, preferredCategories: [], notificationEnabled: false };
  syncFavoriteFlags(new Set());
}

function sortArticles(articles, mode) {
  return [...articles].sort((left, right) => {
    if (mode === "today") {
      const scoreDiff = numericValue(right.totalScore) - numericValue(left.totalScore);
      if (scoreDiff !== 0) {
        return scoreDiff;
      }
    }
    return timeValue(right.processedAt || right.publishedAt) - timeValue(left.processedAt || left.publishedAt);
  });
}

function buildApiUrl(path) {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const baseUrl = state.apiBaseUrl || window.location.origin;
  if (state.apiBaseUrl) {
    return `${baseUrl}${cleanPath.startsWith("/api") ? cleanPath : `/api${cleanPath}`}`;
  }
  return `${baseUrl}${cleanPath}`;
}

function normalizeBaseUrl(value) {
  return value ? value.replace(/\/+$/, "") : "";
}

function formatDate(value) {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatScore(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return Number(value).toFixed(1);
}

function getErrorMessage(error) {
  return error instanceof Error ? error.message : "Unknown error";
}

function numericValue(value) {
  return Number.isFinite(Number(value)) ? Number(value) : -1;
}

function timeValue(value) {
  const timestamp = new Date(value || 0).getTime();
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function loadJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function firstNonEmpty(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return values.at(-1) || "";
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r/g, "").split("\n");
  const blocks = [];
  let inList = false;
  let inCode = false;
  let codeBuffer = [];
  let tableBuffer = [];

  const closeList = () => {
    if (inList) {
      blocks.push("</ul>");
      inList = false;
    }
  };

  const closeTable = () => {
    if (tableBuffer.length) {
      blocks.push(renderTable(tableBuffer));
      tableBuffer = [];
    }
  };

  for (let index = 0; index < lines.length; index += 1) {
    const rawLine = lines[index];
    const line = rawLine.trimEnd();
    const nextLine = index + 1 < lines.length ? lines[index + 1].trim() : "";

    if (line.startsWith("```")) {
      closeList();
      closeTable();
      if (inCode) {
        blocks.push(`<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`);
        inCode = false;
        codeBuffer = [];
      } else {
        inCode = true;
      }
      continue;
    }

    if (inCode) {
      codeBuffer.push(rawLine);
      continue;
    }

    if (isTableDivider(line) && tableBuffer.length) {
      continue;
    }

    if (isTableRow(line) && isTableDivider(nextLine)) {
      closeList();
      tableBuffer.push(line);
      continue;
    }

    if (isTableRow(line) && tableBuffer.length) {
      tableBuffer.push(line);
      continue;
    }

    if (!line.trim()) {
      closeList();
      closeTable();
      continue;
    }

    closeTable();

    if (/^---+$/.test(line.trim())) {
      closeList();
      blocks.push("<hr>");
      continue;
    }
    if (/^####\s+/.test(line)) {
      closeList();
      blocks.push(`<h4>${inlineMarkdown(line.replace(/^####\s+/, ""))}</h4>`);
      continue;
    }
    if (/^###\s+/.test(line)) {
      closeList();
      blocks.push(`<h3>${inlineMarkdown(line.replace(/^###\s+/, ""))}</h3>`);
      continue;
    }
    if (/^##\s+/.test(line)) {
      closeList();
      blocks.push(`<h2>${inlineMarkdown(line.replace(/^##\s+/, ""))}</h2>`);
      continue;
    }
    if (/^#\s+/.test(line)) {
      closeList();
      blocks.push(`<h1>${inlineMarkdown(line.replace(/^#\s+/, ""))}</h1>`);
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      if (!inList) {
        blocks.push("<ul>");
        inList = true;
      }
      blocks.push(`<li>${inlineMarkdown(line.replace(/^[-*]\s+/, ""))}</li>`);
      continue;
    }
    if (/^>\s?/.test(line)) {
      closeList();
      blocks.push(`<blockquote>${inlineMarkdown(line.replace(/^>\s?/, ""))}</blockquote>`);
      continue;
    }

    closeList();
    blocks.push(`<p>${inlineMarkdown(line)}</p>`);
  }

  closeList();
  closeTable();
  if (inCode) {
    blocks.push(`<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`);
  }
  return blocks.join("");
}

function isTableRow(line) {
  const trimmed = line.trim();
  return trimmed.startsWith("|") && trimmed.endsWith("|");
}

function isTableDivider(line) {
  const trimmed = line.trim();
  return /^\|(?:\s*:?-{3,}:?\s*\|)+$/.test(trimmed);
}

function renderTable(lines) {
  if (lines.length < 2) {
    return lines.map((line) => `<p>${inlineMarkdown(line)}</p>`).join("");
  }

  const [headerLine, ...bodyLines] = lines;
  const headers = splitTableCells(headerLine);
  const rows = bodyLines.map(splitTableCells);

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>${headers.map((cell) => `<th>${inlineMarkdown(cell)}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${rows.map((row) => `<tr>${row.map((cell) => `<td>${inlineMarkdown(cell)}</td>`).join("")}</tr>`).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function splitTableCells(line) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function inlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
}
