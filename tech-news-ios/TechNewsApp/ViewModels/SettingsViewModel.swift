import Foundation
import SwiftUI

@MainActor
class SettingsViewModel: ObservableObject {
    @Published var preferences: UserPreference?
    @Published var selectedCategories: Set<String> = []
    @Published var notificationsEnabled = true
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let client = APIClient.shared

    func loadPreferences() async {
        isLoading = true
        errorMessage = nil

        do {
            let response: UserPreferenceResponse = try await client.get(Constants.Endpoints.preferences())
            if let prefs = response.data {
                preferences = prefs
                selectedCategories = Set(prefs.preferredCategories ?? [])
                notificationsEnabled = prefs.notificationEnabled ?? true
            }
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func savePreferences() async {
        isLoading = true
        errorMessage = nil

        let request = UserPreferenceRequest(
            preferredCategories: Array(selectedCategories),
            notificationEnabled: notificationsEnabled
        )

        do {
            let response: UserPreferenceResponse = try await client.put(Constants.Endpoints.preferences(), body: request)
            if let prefs = response.data {
                preferences = prefs
            }
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func toggleCategory(_ category: String) {
        if selectedCategories.contains(category) {
            selectedCategories.remove(category)
        } else {
            selectedCategories.insert(category)
        }
    }
}
