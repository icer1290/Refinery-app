import SwiftUI

struct ContentView: View {
    @State private var selectedTab = 0
    @StateObject private var newsViewModel = NewsViewModel()

    var body: some View {
        TabView(selection: $selectedTab) {
            NewsListView()
                .environmentObject(newsViewModel)
                .tabItem {
                    Label("Today", systemImage: "newspaper")
                }
                .tag(0)

            ArchiveView()
                .environmentObject(newsViewModel)
                .tabItem {
                    Label("Archive", systemImage: "calendar")
                }
                .tag(1)

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
                .tag(2)
        }
        .tint(AppColors.accent)
    }
}

#Preview {
    ContentView()
}