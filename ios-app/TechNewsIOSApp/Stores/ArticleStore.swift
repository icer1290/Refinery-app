import Foundation
import SwiftUI

@MainActor
final class ArticleStore: ObservableObject {
    @Published private(set) var homeArticleIDs: [UUID] = []
    @Published private(set) var favoriteArticleIDs: [UUID] = []
    @Published private(set) var articlesByID: [UUID: Article] = [:]
    @Published private(set) var isLoadingHome = false
    @Published private(set) var isLoadingMore = false
    @Published private(set) var isLoadingFavorites = false
    @Published private(set) var loadingDetailIDs = Set<UUID>()
    @Published private(set) var loadingDeepSearchIDs = Set<UUID>()
    @Published var homeErrorMessage: String?

    private let client: APIClient
    private var availableArchiveDates: [String] = []
    private var nextArchiveDateIndex = 0

    init(client: APIClient) {
        self.client = client
    }

    var homeArticles: [Article] {
        homeArticleIDs.compactMap { articlesByID[$0] }
    }

    var favoriteArticles: [Article] {
        favoriteArticleIDs.compactMap { articlesByID[$0] }
    }

    func article(id: UUID) -> Article? {
        articlesByID[id]
    }

    func refresh(authToken: String?) async {
        isLoadingHome = true
        homeErrorMessage = nil
        availableArchiveDates = []
        nextArchiveDateIndex = 0
        homeArticleIDs = []

        do {
            let todayArticles: [Article] = try await client.request(
                path: "api/news/today",
                token: authToken
            )
            upsert(todayArticles)
            homeArticleIDs = todayArticles.map(\.id)

            let dates: [String] = try await client.request(path: "api/news/dates", token: authToken)
            let todayKey = Self.archiveDateString(for: Date())
            availableArchiveDates = dates.filter { $0 != todayKey }
        } catch {
            homeErrorMessage = error.localizedDescription
        }

        isLoadingHome = false
    }

    func loadNextArchiveDayIfNeeded(currentArticleID: UUID, authToken: String?) async {
        guard
            let currentIndex = homeArticleIDs.firstIndex(of: currentArticleID),
            currentIndex >= homeArticleIDs.count - 3
        else {
            return
        }

        await loadNextArchiveDay(authToken: authToken)
    }

    func loadNextArchiveDay(authToken: String?) async {
        guard !isLoadingMore, nextArchiveDateIndex < availableArchiveDates.count else {
            return
        }

        isLoadingMore = true
        defer { isLoadingMore = false }

        let dateString = availableArchiveDates[nextArchiveDateIndex]
        nextArchiveDateIndex += 1

        do {
            let articles: [Article] = try await client.request(
                path: "api/news/archive",
                queryItems: [
                    URLQueryItem(name: "startDate", value: dateString),
                    URLQueryItem(name: "endDate", value: dateString)
                ],
                token: authToken
            )
            upsert(articles)

            let newIDs = articles.map(\.id).filter { !homeArticleIDs.contains($0) }
            homeArticleIDs.append(contentsOf: newIDs)
        } catch {
            homeErrorMessage = error.localizedDescription
        }
    }

    func loadFavorites(authToken: String?) async {
        guard let authToken else {
            clearAuthenticatedState()
            return
        }

        isLoadingFavorites = true
        defer { isLoadingFavorites = false }

        do {
            let favorites: [Article] = try await client.request(
                path: "api/user/favorites",
                token: authToken
            )
            let favoriteIDs = favorites.map(\.id)
            upsert(favorites)
            syncFavoriteFlags(with: Set(favoriteIDs))
            favoriteArticleIDs = favoriteIDs
        } catch {
            homeErrorMessage = error.localizedDescription
        }
    }

    func clearAuthenticatedState() {
        favoriteArticleIDs = []
        syncFavoriteFlags(with: [])
    }

    func loadArticle(id: UUID, authToken: String?) async {
        if loadingDetailIDs.contains(id) {
            return
        }

        loadingDetailIDs.insert(id)
        defer { loadingDetailIDs.remove(id) }

        do {
            let article: Article = try await client.request(
                path: "api/news/\(id.uuidString)",
                token: authToken
            )
            upsert([article])
            if article.isFavorite, !favoriteArticleIDs.contains(article.id) {
                favoriteArticleIDs.insert(article.id, at: 0)
            }
        } catch {
            homeErrorMessage = error.localizedDescription
        }
    }

    func toggleFavorite(id: UUID, authToken: String?) async throws {
        guard let authToken else {
            throw APIError.unauthorized
        }
        guard var article = articlesByID[id] else {
            return
        }

        let targetValue = !article.isFavorite
        article.isFavorite = targetValue
        articlesByID[id] = article

        if targetValue {
            if !favoriteArticleIDs.contains(id) {
                favoriteArticleIDs.insert(id, at: 0)
            }
        } else {
            favoriteArticleIDs.removeAll { $0 == id }
        }

        do {
            if targetValue {
                try await client.requestEmpty(
                    path: "api/news/\(id.uuidString)/favorite",
                    method: "POST",
                    token: authToken
                )
            } else {
                try await client.requestEmpty(
                    path: "api/news/\(id.uuidString)/favorite",
                    method: "DELETE",
                    token: authToken
                )
            }
        } catch {
            article.isFavorite.toggle()
            articlesByID[id] = article

            if article.isFavorite {
                if !favoriteArticleIDs.contains(id) {
                    favoriteArticleIDs.insert(id, at: 0)
                }
            } else {
                favoriteArticleIDs.removeAll { $0 == id }
            }

            throw error
        }
    }

    func runDeepSearch(id: UUID, authToken: String?) async throws {
        guard let authToken else {
            throw APIError.unauthorized
        }
        guard !loadingDeepSearchIDs.contains(id) else {
            return
        }

        loadingDeepSearchIDs.insert(id)
        defer { loadingDeepSearchIDs.remove(id) }

        let response: DeepSearchResult = try await client.request(
            path: "api/news/\(id.uuidString)/deepsearch",
            method: "POST",
            queryItems: [
                URLQueryItem(name: "maxIterations", value: String(AppConfiguration.deepSearchMaxIterations))
            ],
            body: AnyEncodable(
                DeepSearchRequest(
                    articleID: id.uuidString,
                    maxIterations: AppConfiguration.deepSearchMaxIterations
                )
            ),
            token: authToken
        )

        guard var article = articlesByID[id] else {
            return
        }
        article.deepsearchReport = response.finalReport
        articlesByID[id] = article
    }

    private func upsert(_ articles: [Article]) {
        for article in articles {
            articlesByID[article.id] = article
        }
    }

    private func syncFavoriteFlags(with favorites: Set<UUID>) {
        for id in articlesByID.keys {
            guard var article = articlesByID[id] else { continue }
            article.isFavorite = favorites.contains(id)
            articlesByID[id] = article
        }
    }

    private static func archiveDateString(for date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
}
