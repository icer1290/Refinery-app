import SwiftUI

struct FavoritesView: View {
    @EnvironmentObject private var sessionStore: SessionStore
    @EnvironmentObject private var articleStore: ArticleStore

    var body: some View {
        NavigationStack {
            Group {
                if !sessionStore.isAuthenticated {
                    ContentUnavailableView(
                        "Sign in required",
                        systemImage: "heart.slash",
                        description: Text("Log in to sync your favorite news.")
                    )
                } else if articleStore.isLoadingFavorites && articleStore.favoriteArticles.isEmpty {
                    ProgressView("Loading favorites...")
                } else if articleStore.favoriteArticles.isEmpty {
                    ContentUnavailableView(
                        "No favorites yet",
                        systemImage: "heart",
                        description: Text("Tap the heart on a story to save it.")
                    )
                } else {
                    List(articleStore.favoriteArticles) { article in
                        NavigationLink {
                            ArticleDetailView(articleID: article.id)
                        } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(article.displayTitle)
                                    .font(.headline)
                                Text(article.displayPreview)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(2)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .listStyle(.insetGrouped)
                }
            }
            .navigationTitle("Favorites")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    if !sessionStore.isAuthenticated {
                        Button("Sign In") {
                            sessionStore.presentAuthSheet()
                        }
                    }
                }
            }
            .task(id: sessionStore.token) {
                await articleStore.loadFavorites(authToken: sessionStore.token)
            }
        }
    }
}
