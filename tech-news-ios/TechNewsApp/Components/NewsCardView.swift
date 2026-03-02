import SwiftUI

// MARK: - News Card View

/// A styled card view for displaying news items in a list
/// Features source label, score badge, title, summary, and category tag
struct NewsCardView: View {
    let news: News
    var showDate: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: DesignTokens.cardSpacing) {
            // Header: Source + Score
            headerView

            // Title
            titleView

            // Summary
            if let summary = news.summary, !summary.isEmpty {
                summaryView(summary)
            }

            // Footer: Category tag
            footerView
        }
        .padding(DesignTokens.cardPadding)
        .background(AppColors.surface)
        .cornerRadius(DesignTokens.radiusM)
        .overlay(
            RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                .stroke(AppColors.border, lineWidth: DesignTokens.borderWidth)
        )
    }

    // MARK: - Header View

    private var headerView: some View {
        HStack(alignment: .center) {
            // Source label
            if let source = news.source {
                SourceLabel(source: source)
            }

            Spacer()

            // Score badge (uses llmScore for better distribution)
            if let llmScore = news.llmScore {
                ScoreBadge(llmScore: llmScore)
            } else if showDate {
                // Show date for archive view
                Text(news.formattedDate)
                    .font(AppTypography.monoCaption())
                    .foregroundColor(AppColors.secondary)
            }
        }
    }

    // MARK: - Title View

    private var titleView: some View {
        Text(news.displayTitle)
            .font(AppTypography.headline())
            .foregroundColor(AppColors.primary)
            .lineLimit(2)
            .multilineTextAlignment(.leading)
    }

    // MARK: - Summary View

    private func summaryView(_ summary: String) -> some View {
        Text(summary)
            .font(AppTypography.body())
            .foregroundColor(AppColors.secondary)
            .lineLimit(2)
            .multilineTextAlignment(.leading)
    }

    // MARK: - Footer View

    private var footerView: some View {
        HStack {
            if let category = news.category {
                CategoryTag(category: category)
            }

            Spacer()

            if showDate, let _ = news.llmScore {
                Text(news.formattedDate)
                    .font(AppTypography.monoCaption())
                    .foregroundColor(AppColors.secondary)
            }
        }
    }
}

// MARK: - Preview

#Preview("News Card") {
    VStack(spacing: 16) {
        NewsCardView(news: News(
            id: 1,
            title: "Apple Announces New AI Features for iOS 18",
            translatedTitle: nil,
            url: "https://example.com",
            source: "TechCrunch",
            category: "AI & Machine Learning",
            score: 100,
            llmScore: 9.2,
            finalScore: 0.92,
            summary: "Apple has announced groundbreaking AI features coming to iOS 18, including advanced on-device processing and Siri improvements.",
            publishedDate: "2024-01-15",
            isFavorite: false
        ))

        NewsCardView(news: News(
            id: 2,
            title: "OpenAI Releases GPT-5 with Enhanced Reasoning",
            translatedTitle: nil,
            url: "https://example.com",
            source: "The Verge",
            category: "AI",
            score: 85,
            llmScore: 7.5,
            finalScore: 0.75,
            summary: "The latest model shows significant improvements in logical reasoning and coding tasks.",
            publishedDate: "2024-01-14",
            isFavorite: false
        ))

        NewsCardView(news: News(
            id: 3,
            title: "Quick Update",
            translatedTitle: nil,
            url: "https://example.com",
            source: "Hacker News",
            category: nil,
            score: 50,
            llmScore: 4.0,
            finalScore: 0.40,
            summary: nil,
            publishedDate: "2024-01-13",
            isFavorite: false
        ))
    }
    .padding()
    .background(AppColors.background)
}