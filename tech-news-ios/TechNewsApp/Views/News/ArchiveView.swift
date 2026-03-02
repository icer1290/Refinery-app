import SwiftUI

struct ArchiveView: View {
    @EnvironmentObject var newsViewModel: NewsViewModel
    @State private var selectedMonth = Date()

    var body: some View {
        NavigationStack {
            ZStack {
                if newsViewModel.isLoading && newsViewModel.archiveNews.isEmpty {
                    LoadingStateView("Loading archive...")
                } else if newsViewModel.archiveNews.isEmpty {
                    EmptyStateView(
                        icon: "calendar.badge.exclamationmark",
                        title: "No News in Archive",
                        subtitle: "Try selecting a different month"
                    )
                } else {
                    newsList
                }
            }
            .background(AppColors.background)
            .navigationTitle("Archive")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    datePicker
                }
            }
            .task {
                await newsViewModel.loadArchiveNews()
            }
        }
    }

    private var newsList: some View {
        ScrollView {
            LazyVStack(spacing: DesignTokens.spacingM) {
                ForEach(newsViewModel.archiveNews) { news in
                    NavigationLink(value: news) {
                        NewsCardView(news: news, showDate: true)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal, DesignTokens.spacingM)
            .padding(.vertical, DesignTokens.spacingS)
        }
        .navigationDestination(for: News.self) { news in
            NewsDetailView(news: news)
                .environmentObject(newsViewModel)
        }
    }

    private var datePicker: some View {
        DatePicker(
            "",
            selection: $selectedMonth,
            displayedComponents: [.date]
        )
        .labelsHidden()
        .tint(AppColors.accent)
        .onChange(of: selectedMonth) { _ in
            Task {
                await newsViewModel.loadArchiveNews()
            }
        }
    }
}

#Preview {
    ArchiveView()
        .environmentObject(NewsViewModel())
}