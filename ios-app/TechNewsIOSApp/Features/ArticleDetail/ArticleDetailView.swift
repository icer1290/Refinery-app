import MarkdownUI
import SwiftUI

struct ArticleDetailView: View {
    let articleID: UUID

    @EnvironmentObject private var sessionStore: SessionStore
    @EnvironmentObject private var articleStore: ArticleStore

    var body: some View {
        ScrollView {
            if let article = articleStore.article(id: articleID) {
                VStack(alignment: .leading, spacing: 20) {
                    VStack(alignment: .leading, spacing: 12) {
                        Text(article.displayTitle)
                            .font(.title2)
                            .fontWeight(.bold)

                        Label(
                            "Score \(article.totalScore.map { String(format: "%.1f", $0) } ?? "--")",
                            systemImage: "chart.bar.xaxis"
                        )
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                        Text(article.chineseSummary ?? article.displayPreview)
                            .font(.body)
                            .foregroundStyle(.primary)

                        HStack {
                            Text(article.sourceName ?? "Unknown source")
                            Spacer()
                            Text(DateFormatting.detailTimestamp(article.publishedAt))
                        }
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                    }

                    deepSearchSection(article: article)
                }
                .padding(20)
            } else if articleStore.loadingDetailIDs.contains(articleID) {
                ProgressView("Loading article...")
                    .frame(maxWidth: .infinity, minHeight: 320)
            } else {
                ContentUnavailableView("Article not found", systemImage: "doc.text.magnifyingglass")
                    .frame(maxWidth: .infinity, minHeight: 320)
            }
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("Detail")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    Task {
                        await toggleFavorite()
                    }
                } label: {
                    Image(systemName: (articleStore.article(id: articleID)?.isFavorite ?? false) ? "heart.fill" : "heart")
                        .foregroundStyle((articleStore.article(id: articleID)?.isFavorite ?? false) ? .red : .secondary)
                }
            }
        }
        .task {
            await articleStore.loadArticle(id: articleID, authToken: sessionStore.token)
        }
    }

    @ViewBuilder
    private func deepSearchSection(article: Article) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("DeepSearch")
                    .font(.title3)
                    .fontWeight(.semibold)
                Spacer()
                if articleStore.loadingDeepSearchIDs.contains(articleID) {
                    ProgressView()
                }
            }

            if let report = article.deepsearchReport, !report.isEmpty {
                DeepSearchReportView(report: report)

                if let performedAt = article.deepsearchPerformedAt {
                    Text("Updated \(DateFormatting.detailTimestamp(performedAt))")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            } else {
                Text("Generate a deeper tracking report for this story.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Button {
                    Task {
                        await runDeepSearch()
                    }
                } label: {
                    Label("Run DeepSearch", systemImage: "sparkles.magnifyingglass")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(articleStore.loadingDeepSearchIDs.contains(articleID))
            }
        }
        .padding(18)
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(Color(.secondarySystemBackground))
        )
    }

    private func toggleFavorite() async {
        do {
            try await articleStore.toggleFavorite(id: articleID, authToken: sessionStore.token)
        } catch APIError.unauthorized {
            sessionStore.presentAuthSheet()
        } catch {
            articleStore.homeErrorMessage = error.localizedDescription
        }
    }

    private func runDeepSearch() async {
        do {
            try await articleStore.runDeepSearch(id: articleID, authToken: sessionStore.token)
        } catch APIError.unauthorized {
            sessionStore.presentAuthSheet()
        } catch {
            articleStore.homeErrorMessage = error.localizedDescription
        }
    }
}

private struct DeepSearchReportView: View {
    let report: String

    var body: some View {
        Group {
            if report.isEmpty {
                EmptyView()
            } else if let content = try? MarkdownContent(report) {
                Markdown(content)
                    .markdownTheme(.techNewsDeepSearch)
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
            } else if let attributed = try? AttributedString(markdown: report) {
                Text(attributed)
                    .font(.body)
                    .foregroundStyle(.primary)
                    .frame(maxWidth: .infinity, alignment: .leading)
            } else {
                Text(report)
                    .font(.body)
                    .foregroundStyle(.primary)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }
}
