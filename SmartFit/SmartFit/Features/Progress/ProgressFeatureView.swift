import SwiftUI

struct ProgressFeatureView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            ProgressOverviewView(repository: appState.environment.progressRepository)
        }
    }
}

enum WorkoutDateFormatting {
    static let apiFormatters: [ISO8601DateFormatter] = {
        let withFraction = ISO8601DateFormatter()
        withFraction.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let withoutFraction = ISO8601DateFormatter()
        withoutFraction.formatOptions = [.withInternetDateTime]
        return [withFraction, withoutFraction]
    }()

    static func displayDateTime(from raw: String) -> String {
        for formatter in apiFormatters {
            if let date = formatter.date(from: raw) {
                return date.formatted(date: .abbreviated, time: .shortened)
            }
        }
        return raw
    }
}
