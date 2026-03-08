import SwiftUI

@main
struct TechNewsIOSApp: App {
    @StateObject private var sessionStore: SessionStore
    @StateObject private var articleStore: ArticleStore
    @StateObject private var preferencesStore: PreferencesStore

    init() {
        let client = APIClient()
        _sessionStore = StateObject(wrappedValue: SessionStore(client: client))
        _articleStore = StateObject(wrappedValue: ArticleStore(client: client))
        _preferencesStore = StateObject(wrappedValue: PreferencesStore(client: client))
    }

    var body: some Scene {
        WindowGroup {
            RootTabView()
                .environmentObject(sessionStore)
                .environmentObject(articleStore)
                .environmentObject(preferencesStore)
        }
    }
}
