import SwiftUI

struct NewsDetailView: View {
    let news: News
    @EnvironmentObject var newsViewModel: NewsViewModel
    @Environment(\.openURL) var openURL
    @State private var showShareSheet = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: DesignTokens.spacingL) {
                // Header Section
                headerSection

                // Summary Section
                if let summary = news.summary, !summary.isEmpty {
                    summarySection(summary)
                }

                Spacer()

                // Actions Section
                actionsSection
            }
            .padding(DesignTokens.spacingM)
        }
        .background(AppColors.background)
        .navigationTitle("Details")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showShareSheet) {
            if let url = URL(string: news.url) {
                ShareSheet(items: [url])
            }
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacingM) {
            // Source and Score Row
            HStack(alignment: .center) {
                if let source = news.source {
                    SourceLabel(source: source, style: .prominent)
                }

                Spacer()

                if let score = news.finalScore {
                    ScoreBadge(score: score)
                }
            }

            // Title
            Text(news.displayTitle)
                .font(AppTypography.title())
                .foregroundColor(AppColors.primary)
                .fixedSize(horizontal: false, vertical: true)

            // Category and Date Row
            HStack {
                if let category = news.category {
                    CategoryTag(category: category, style: .prominent)
                }

                Spacer()

                if !news.formattedDate.isEmpty {
                    Text(news.formattedDate)
                        .font(AppTypography.monoCaption())
                        .foregroundColor(AppColors.secondary)
                }
            }
        }
        .padding(DesignTokens.cardPadding)
        .background(AppColors.surface)
        .cornerRadius(DesignTokens.radiusM)
        .overlay(
            RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                .stroke(AppColors.border, lineWidth: DesignTokens.borderWidth)
        )
    }

    // MARK: - Summary Section

    private func summarySection(_ summary: String) -> some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacingS) {
            // Section Header
            HStack(spacing: 8) {
                RoundedRectangle(cornerRadius: 1)
                    .fill(AppColors.accent)
                    .frame(width: 3, height: 16)

                Text("Summary")
                    .font(AppTypography.headline())
                    .foregroundColor(AppColors.primary)
            }

            // Summary Text
            Text(summary)
                .font(AppTypography.body())
                .foregroundColor(AppColors.primary)
                .lineSpacing(4)
        }
        .padding(DesignTokens.cardPadding)
        .background(AppColors.surface)
        .cornerRadius(DesignTokens.radiusM)
        .overlay(
            RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                .stroke(AppColors.border, lineWidth: DesignTokens.borderWidth)
        )
    }

    // MARK: - Actions Section

    private var actionsSection: some View {
        VStack(spacing: DesignTokens.spacingM) {
            // Primary Action
            if let url = URL(string: news.url) {
                ActionButton("Read Full Article", icon: "safari", style: .filled) {
                    openURL(url)
                }
            }

            // Secondary Actions
            HStack(spacing: DesignTokens.spacingM) {
                ActionButton(
                    news.isFavorite == true ? "Unfavorite" : "Favorite",
                    icon: news.isFavorite == true ? "heart.fill" : "heart",
                    style: .bordered
                ) {
                    Task {
                        await newsViewModel.toggleFavorite(news: news)
                    }
                }

                ActionButton("Share", icon: "square.and.arrow.up", style: .bordered) {
                    showShareSheet = true
                }
            }
        }
        .padding(.top, DesignTokens.spacingM)
    }
}

struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

#Preview {
    NavigationStack {
        NewsDetailView(news: News(
            id: 1,
            title: "Sample News Title with a Longer Headline to Test Wrapping",
            translatedTitle: nil,
            url: "https://example.com",
            source: "TechCrunch",
            category: "AI & Machine Learning",
            score: 100,
            llmScore: 8.5,
            finalScore: 0.85,
            summary: "This is a sample summary of the news article. It provides a brief overview of the content and key points.",
            publishedDate: "2024-01-15",
            isFavorite: false
        ))
    }
    .environmentObject(NewsViewModel())
}