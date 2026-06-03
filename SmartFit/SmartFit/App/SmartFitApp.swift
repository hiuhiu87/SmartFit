import SwiftUI

@main
struct SmartFitApp: App {
    @StateObject private var appState: AppState

    init() {
        let environment = AppEnvironment.bootstrap()
        _appState = StateObject(wrappedValue: AppState(environment: environment))
    }

    var body: some Scene {
        WindowGroup {
            AppRouter()
                .environmentObject(appState)
                .preferredColorScheme(.dark)
        }
    }
}
