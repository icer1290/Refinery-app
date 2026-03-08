import SwiftUI

private enum AuthMode: String, CaseIterable, Identifiable {
    case login = "Login"
    case register = "Register"

    var id: String { rawValue }
}

struct AuthFlowView: View {
    @EnvironmentObject private var sessionStore: SessionStore
    @State private var mode: AuthMode = .login
    @State private var email = ""
    @State private var password = ""
    @State private var nickname = ""

    var body: some View {
        Form {
            Picker("Mode", selection: $mode) {
                ForEach(AuthMode.allCases) { mode in
                    Text(mode.rawValue).tag(mode)
                }
            }
            .pickerStyle(.segmented)

            Section("Account") {
                TextField("Email", text: $email)
                    .keyboardType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()

                SecureField("Password", text: $password)

                if mode == .register {
                    TextField("Nickname", text: $nickname)
                }
            }

            if let errorMessage = sessionStore.authErrorMessage {
                Section {
                    Text(errorMessage)
                        .font(.footnote)
                        .foregroundStyle(.red)
                }
            }

            Section {
                Button {
                    Task {
                        await submit()
                    }
                } label: {
                    if sessionStore.isSubmitting {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text(mode == .login ? "Sign In" : "Create Account")
                            .frame(maxWidth: .infinity)
                    }
                }
                .disabled(!canSubmit || sessionStore.isSubmitting)
            }
        }
        .navigationTitle("Account")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Close") {
                    sessionStore.dismissAuthSheet()
                }
            }
        }
    }

    private var canSubmit: Bool {
        if mode == .register {
            return !email.isEmpty && !password.isEmpty && !nickname.isEmpty
        }
        return !email.isEmpty && !password.isEmpty
    }

    private func submit() async {
        switch mode {
        case .login:
            _ = await sessionStore.login(email: email, password: password)
        case .register:
            _ = await sessionStore.register(email: email, password: password, nickname: nickname)
        }
    }
}
