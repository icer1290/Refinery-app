import SwiftUI

struct ProfileView: View {
    @EnvironmentObject private var sessionStore: SessionStore
    @EnvironmentObject private var preferencesStore: PreferencesStore
    @State private var serverURLText = AppConfiguration.persistedAPIBaseURLString ?? AppConfiguration.apiBaseURLString
    @State private var serverURLMessage: String?

    var body: some View {
        NavigationStack {
            Group {
                if let session = sessionStore.session {
                    Form {
                        serverSection

                        Section("Account") {
                            LabeledContent("Nickname", value: session.nickname ?? "Not set")
                            LabeledContent("Email", value: session.email)
                            LabeledContent("User ID", value: String(session.userID))
                        }

                        Section("Preferences") {
                            TextField("AI, LLM, Chips", text: $preferencesStore.categoriesText, axis: .vertical)
                            Toggle("Notifications", isOn: Binding(
                                get: { preferencesStore.preferences.notificationEnabled },
                                set: { preferencesStore.preferences.notificationEnabled = $0 }
                            ))

                            Button {
                                Task {
                                    await preferencesStore.save(authToken: sessionStore.token)
                                }
                            } label: {
                                if preferencesStore.isSaving {
                                    ProgressView()
                                        .frame(maxWidth: .infinity)
                                } else {
                                    Text("Save Preferences")
                                        .frame(maxWidth: .infinity)
                                }
                            }
                            .disabled(preferencesStore.isSaving)
                        }

                        if let errorMessage = preferencesStore.errorMessage {
                            Section {
                                Text(errorMessage)
                                    .font(.footnote)
                                    .foregroundStyle(.red)
                            }
                        }

                        Section {
                            Button("Log Out", role: .destructive) {
                                sessionStore.logout()
                                preferencesStore.reset()
                            }
                        }
                    }
                    .overlay {
                        if preferencesStore.isLoading {
                            ProgressView()
                        }
                    }
                    .task(id: session.token) {
                        await preferencesStore.load(authToken: sessionStore.token)
                    }
                } else {
                    Form {
                        serverSection

                        Section {
                            ContentUnavailableView(
                                "No account",
                                systemImage: "person.crop.circle.badge.exclamationmark",
                                description: Text("Sign in or create an account to manage favorites and preferences.")
                            )
                            .frame(maxWidth: .infinity)
                            .listRowInsets(EdgeInsets())
                            .padding(.vertical, 20)
                        }
                    }
                }
            }
            .navigationTitle("Profile")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    if !sessionStore.isAuthenticated {
                        Button("Sign In") {
                            sessionStore.presentAuthSheet()
                        }
                    }
                }
            }
        }
    }

    private var serverSection: some View {
        Section("Server") {
            TextField("http://192.168.x.x:8080", text: $serverURLText)
                .textInputAutocapitalization(.never)
                .keyboardType(.URL)
                .autocorrectionDisabled()

            Button("Save Server URL") {
                let normalized = AppConfiguration.normalizeBaseURLString(serverURLText)
                AppConfiguration.saveAPIBaseURLString(serverURLText)
                serverURLText = normalized ?? AppConfiguration.apiBaseURLString
                serverURLMessage = normalized == nil
                    ? "Server URL reset to app default."
                    : "Server URL saved. On iPhone, use your Mac's LAN IP, not localhost."
            }

            Button("Use App Default") {
                AppConfiguration.clearAPIBaseURLOverride()
                serverURLText = AppConfiguration.apiBaseURLString
                serverURLMessage = "Reverted to app default."
            }
            .foregroundStyle(.secondary)

            Text("Simulator can use `http://localhost:8080`. On a physical iPhone, use your Mac's LAN IP, for example `http://192.168.1.23:8080`.")
                .font(.footnote)
                .foregroundStyle(.secondary)

            if let serverURLMessage {
                Text(serverURLMessage)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
    }
}
