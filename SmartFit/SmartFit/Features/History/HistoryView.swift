import SwiftUI

struct HistoryView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            WorkoutHistoryView(repository: appState.environment.historyRepository)
        }
    }
}
