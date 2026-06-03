import SwiftUI

struct ServerConfigurationSection: View {
    enum DisplayStyle {
        case authEntry
        case settingsPanel
    }

    @EnvironmentObject private var appState: AppState
    @State private var baseURLInput = ""
    @State private var errorMessage: String?
    @State private var isPresentingSheet = false
    @State private var isExpanded = false

    let style: DisplayStyle

    init(style: DisplayStyle = .authEntry) {
        self.style = style
    }

    var body: some View {
        Group {
            switch style {
            case .authEntry:
                authEntry
            case .settingsPanel:
                settingsPanel
            }
        }
        .sheet(isPresented: $isPresentingSheet) {
            NavigationStack {
                ScrollView {
                    configurationContent
                        .padding(20)
                }
                .background(AppColors.background.ignoresSafeArea())
                .navigationTitle("Developer Server")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Done") {
                            isPresentingSheet = false
                        }
                        .foregroundStyle(AppColors.primary)
                    }
                }
            }
            .presentationDetents([.medium, .large])
        }
        .onAppear {
            syncInputFromStore()
        }
    }

    private var authEntry: some View {
        HStack(spacing: 10) {
            Image(systemName: "antenna.radiowaves.left.and.right")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppColors.textSecondary)

            Button {
                syncInputFromStore()
                isPresentingSheet = true
            } label: {
                Text("Using a local dev server?")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
                    .underline(true, color: AppColors.border)
            }
            .buttonStyle(.plain)

            Spacer(minLength: 0)
        }
        .padding(.top, 4)
    }

    private var settingsPanel: some View {
        AppCard(cornerRadius: 18, padding: 16) {
            VStack(alignment: .leading, spacing: 14) {
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        isExpanded.toggle()
                    }
                } label: {
                    HStack(spacing: 12) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Developer Server")
                                .font(AppTypography.title)
                                .foregroundStyle(AppColors.textPrimary)
                            Text("Override API base URL for local backend testing.")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.textSecondary)
                        }

                        Spacer()

                        Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(AppColors.textSecondary)
                    }
                }
                .buttonStyle(.plain)

                if isExpanded {
                    configurationContent
                        .transition(.opacity.combined(with: .move(edge: .top)))
                }
            }
        }
    }

    private var configurationContent: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("This is only for development. Use your Mac's LAN IP when testing on a real device.")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)

            AppInputField {
                TextField("http://192.168.1.23:8000", text: $baseURLInput)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .keyboardType(.URL)
                    .font(AppTypography.body)
            }

            VStack(alignment: .leading, spacing: 6) {
                Text("Current: \(appState.environment.baseURL.absoluteString)")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
                    .textSelection(.enabled)

                if let customURL = appState.environment.baseURLStore.customBaseURL {
                    Text("Override: \(customURL.absoluteString)")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                        .textSelection(.enabled)
                } else {
                    Text("Override: Not set")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }
            }

            if let errorMessage {
                Text(errorMessage)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.error)
            }

            VStack(spacing: 10) {
                PrimaryButton(title: "Save Server URL") {
                    save()
                }

                SecondaryButton(title: "Reset to Default") {
                    appState.environment.baseURLStore.clearCustomBaseURL()
                    syncInputFromStore()
                    errorMessage = nil
                }
            }
        }
    }

    private func syncInputFromStore() {
        baseURLInput = appState.environment.baseURL.absoluteString
    }

    private func save() {
        do {
            try appState.environment.baseURLStore.saveCustomBaseURL(baseURLInput)
            syncInputFromStore()
            errorMessage = nil
        } catch {
            errorMessage = "Invalid URL. Use http://<your-mac-ip>:8000 or https://..."
        }
    }
}
