import Foundation
import SwiftUI

@MainActor
class NewsViewModel: ObservableObject {
    @Published var todayNews: [News] = []
    @Published var archiveNews: [News] = []
    @Published var favoriteNews: [News] = []
    @Published var availableDates: [String] = []
    @Published var selectedNews: News?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var selectedDate: Date = Date()

    private let newsService = NewsService()

    func loadTodayNews() async {
        isLoading = true
        errorMessage = nil

        do {
            todayNews = try await newsService.getTodayNews()
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func loadArchiveNews() async {
        isLoading = true
        errorMessage = nil

        let calendar = Calendar.current
        let startOfMonth = calendar.date(from: calendar.dateComponents([.year, .month], from: selectedDate))!
        let endOfMonth = calendar.date(byAdding: DateComponents(month: 1, day: -1), to: startOfMonth)!

        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withFullDate]

        do {
            archiveNews = try await newsService.getArchiveNews(
                startDate: formatter.string(from: startOfMonth),
                endDate: formatter.string(from: endOfMonth)
            )
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func loadAvailableDates() async {
        do {
            availableDates = try await newsService.getAvailableDates()
        } catch {
            print("Failed to load available dates: \(error)")
        }
    }

    func loadNewsDetail(id: Int) async {
        isLoading = true
        errorMessage = nil

        do {
            selectedNews = try await newsService.getNewsDetail(id: id)
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func toggleFavorite(news: News) async {
        guard let newsId = news.id as Int? else { return }

        do {
            if news.isFavorite == true {
                try await newsService.removeFavorite(newsId: newsId)
            } else {
                try await newsService.addFavorite(newsId: newsId)
            }

            // Update local state
            if let index = todayNews.firstIndex(where: { $0.id == news.id }) {
                var updatedNews = todayNews[index]
                todayNews[index] = News(
                    id: updatedNews.id,
                    title: updatedNews.title,
                    translatedTitle: updatedNews.translatedTitle,
                    url: updatedNews.url,
                    source: updatedNews.source,
                    category: updatedNews.category,
                    score: updatedNews.score,
                    llmScore: updatedNews.llmScore,
                    finalScore: updatedNews.finalScore,
                    summary: updatedNews.summary,
                    publishedDate: updatedNews.publishedDate,
                    isFavorite: !(updatedNews.isFavorite ?? false)
                )
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func loadFavorites() async {
        isLoading = true
        errorMessage = nil

        do {
            favoriteNews = try await newsService.getUserFavorites()
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }
}
