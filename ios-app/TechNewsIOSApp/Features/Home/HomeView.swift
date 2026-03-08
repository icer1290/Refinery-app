import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var sessionStore: SessionStore
    @EnvironmentObject private var articleStore: ArticleStore

    var body: some View {
        NavigationStack {
            Group {
                if articleStore.isLoadingHome && articleStore.homeArticles.isEmpty {
                    ProgressView("Loading news...")
                } else if articleStore.homeArticles.isEmpty {
                    ContentUnavailableView(
                        "No news yet",
                        systemImage: "newspaper",
                        description: Text(articleStore.homeErrorMessage ?? "Pull to refresh.")
                    )
                } else {
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            ForEach(articleStore.homeArticles) { article in
                                NavigationLink {
                                    ArticleDetailView(articleID: article.id)
                                } label: {
                                    NewsCard(article: article) {
                                        Task {
                                            await toggleFavorite(articleID: article.id)
                                        }
                                    }
                                }
                                .buttonStyle(.plain)
                                .task {
                                    await articleStore.loadNextArchiveDayIfNeeded(
                                        currentArticleID: article.id,
                                        authToken: sessionStore.token
                                    )
                                }
                            }

                            if articleStore.isLoadingMore {
                                ProgressView()
                                    .padding(.vertical, 24)
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 20)
                    }
                    .refreshable {
                        await articleStore.refresh(authToken: sessionStore.token)
                        await articleStore.loadFavorites(authToken: sessionStore.token)
                    }
                }
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Today")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    if sessionStore.isAuthenticated {
                        Text("Signed In")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

    private func toggleFavorite(articleID: UUID) async {
        do {
            try await articleStore.toggleFavorite(id: articleID, authToken: sessionStore.token)
        } catch APIError.unauthorized {
            sessionStore.presentAuthSheet()
        } catch {
            articleStore.homeErrorMessage = error.localizedDescription
        }
    }
}
