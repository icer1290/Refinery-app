import SwiftUI

struct RootTabView: View {
    @EnvironmentObject private var sessionStore: SessionStore
    @EnvironmentObject private var articleStore: ArticleStore
    @EnvironmentObject private var preferencesStore: PreferencesStore

    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "newspaper")
                }

            FavoritesView()
                .tabItem {
                    Label("Favorites", systemImage: "heart")
                }

            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.crop.circle")
                }
        }
        .sheet(isPresented: $sessionStore.authSheetPresented) {
            NavigationStack {
                AuthFlowView()
            }
            .presentationDetents([.large])
        }
        .task {
            await reloadAll()
        }
        .onChange(of: sessionStore.token) { _, _ in
            Task {
                await reloadAll()
            }
        }
    }

    private func reloadAll() async {
        await articleStore.refresh(authToken: sessionStore.token)
        await articleStore.loadFavorites(authToken: sessionStore.token)
        await preferencesStore.load(authToken: sessionStore.token)
    }
}
