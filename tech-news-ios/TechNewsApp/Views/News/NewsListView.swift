import SwiftUI

struct NewsListView: View {
    @EnvironmentObject var newsViewModel: NewsViewModel
    @EnvironmentObject var authViewModel: AuthViewModel

    var body: some View {
        NavigationStack {
            ZStack {
                if newsViewModel.isLoading && newsViewModel.todayNews.isEmpty {
                    LoadingStateView("Loading news...")
                } else if newsViewModel.todayNews.isEmpty {
                    EmptyStateView(
                        icon: "newspaper",
                        title: "No News Available",
                        subtitle: "Check back later for the latest tech news",
                        action: EmptyStateView.EmptyStateAction(title: "Refresh") {
                            Task {
                                await newsViewModel.loadTodayNews()
                            }
                        }
                    )
                } else {
                    newsList
                }
            }
            .background(AppColors.background)
            .navigationTitle("Today")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    IconButton(icon: "arrow.clockwise", style: .bordered) {
                        Task {
                            await newsViewModel.loadTodayNews()
                        }
                    }
                }
            }
            .task {
                await newsViewModel.loadTodayNews()
            }
            .refreshable {
                await newsViewModel.loadTodayNews()
            }
        }
    }

    private var newsList: some View {
        ScrollView {
            LazyVStack(spacing: DesignTokens.spacingM) {
                ForEach(newsViewModel.todayNews) { news in
                    NavigationLink(value: news) {
                        NewsCardView(news: news)
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
}

#Preview {
    NewsListView()
        .environmentObject(NewsViewModel())
        .environmentObject(AuthViewModel())
}