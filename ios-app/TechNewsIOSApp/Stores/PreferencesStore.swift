import Foundation
import SwiftUI

@MainActor
final class PreferencesStore: ObservableObject {
    @Published var preferences = UserPreferences(id: nil, preferredCategories: [], notificationEnabled: false)
    @Published var categoriesText = ""
    @Published var isLoading = false
    @Published var isSaving = false
    @Published var errorMessage: String?

    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func load(authToken: String?) async {
        guard let authToken else {
            reset()
            return
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let response: UserPreferences = try await client.request(
                path: "api/user/preferences",
                token: authToken
            )
            preferences = response
            categoriesText = response.preferredCategories.joined(separator: ", ")
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func save(authToken: String?) async {
        guard let authToken else {
            errorMessage = APIError.unauthorized.localizedDescription
            return
        }

        isSaving = true
        errorMessage = nil
        defer { isSaving = false }

        let categories = categoriesText
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        do {
            let updated: UserPreferences = try await client.request(
                path: "api/user/preferences",
                method: "PUT",
                body: AnyEncodable(
                    UserPreferencesRequest(
                        preferredCategories: categories,
                        notificationEnabled: preferences.notificationEnabled
                    )
                ),
                token: authToken
            )
            preferences = updated
            categoriesText = updated.preferredCategories.joined(separator: ", ")
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func reset() {
        preferences = UserPreferences(id: nil, preferredCategories: [], notificationEnabled: false)
        categoriesText = ""
        errorMessage = nil
    }
}
