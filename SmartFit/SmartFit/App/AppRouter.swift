import SwiftUI

struct AppRouter: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        Group {
            if appState.isLoadingInitialSession {
                LoadingView(message: "Loading SmartFit...")
            } else if !appState.isAuthenticated {
                authFlow
            } else if !appState.hasCompletedOnboarding {
                OnboardingView()
            } else {
                MainTabView()
            }
        }
        .animation(.easeInOut, value: appState.isAuthenticated)
    }

    private var authFlow: some View {
        NavigationStack {
            switch appState.authRoute {
            case .welcome:
                WelcomeView()
            case .login:
                LoginView()
            case .register:
                RegisterView()
            }
        }
    }
}

struct MainTabView: View {
    var body: some View {
        TabView {
            TodayView()
                .tabItem {
                    Label("Today", systemImage: "sun.max.fill")
                }

            HistoryView()
                .tabItem {
                    Label("History", systemImage: "clock.arrow.circlepath")
                }

            ProgressFeatureView()
                .tabItem {
                    Label("Progress", systemImage: "chart.line.uptrend.xyaxis")
                }

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape.fill")
                }
        }
        .tint(AppColors.primary)
        .toolbarBackground(AppColors.backgroundSecondary, for: .tabBar)
        .toolbarBackground(.visible, for: .tabBar)
    }
}
