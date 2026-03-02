import Foundation

class NewsService {
    private let client = APIClient.shared

    func getTodayNews() async throws -> [News] {
        let response: NewsListResponse = try await client.get(Constants.Endpoints.todayNews())
        return response.data ?? []
    }

    func getArchiveNews(startDate: String?, endDate: String?) async throws -> [News] {
        var endpoint = Constants.Endpoints.archiveNews()
        var params: [String] = []

        if let start = startDate {
            params.append("startDate=\(start)")
        }
        if let end = endDate {
            params.append("endDate=\(end)")
        }

        if !params.isEmpty {
            endpoint += "?" + params.joined(separator: "&")
        }

        let response: NewsListResponse = try await client.get(endpoint)
        return response.data ?? []
    }

    func getNewsDetail(id: Int) async throws -> News? {
        struct NewsDetailResponse: Codable {
            let success: Bool?
            let data: News?
        }

        let response: NewsDetailResponse = try await client.get(Constants.Endpoints.newsDetail(id: id))
        return response.data
    }

    func getAvailableDates() async throws -> [String] {
        let response: DateListResponse = try await client.get(Constants.Endpoints.availableDates())
        return response.data ?? []
    }

    func addFavorite(newsId: Int) async throws {
        let _: ApiResponse<Empty> = try await client.post(Constants.Endpoints.favorite(id: newsId))
    }

    func removeFavorite(newsId: Int) async throws {
        try await client.delete(Constants.Endpoints.favorite(id: newsId))
    }

    func getUserFavorites() async throws -> [News] {
        struct FavoritesResponse: Codable {
            let success: Bool?
            let data: [News]?
        }

        let response: FavoritesResponse = try await client.get(Constants.Endpoints.userFavorites())
        return response.data ?? []
    }
}

struct Empty: Codable {}
