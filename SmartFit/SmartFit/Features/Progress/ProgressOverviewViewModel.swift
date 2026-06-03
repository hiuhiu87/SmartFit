import Combine
import Foundation

@MainActor
final class ProgressOverviewViewModel: ObservableObject {
    @Published var overview: ProgressOverviewResponse?
    @Published var personalRecords: [PersonalRecordItem] = []
    @Published var weeklyReport: WeeklyReportResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let repository: ProgressRepositoryProtocol

    init(repository: ProgressRepositoryProtocol) {
        self.repository = repository
    }

    func load() async {
        guard overview == nil, personalRecords.isEmpty, weeklyReport == nil else { return }
        await refresh()
    }

    func refresh() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        var partialFailures: [String] = []

        do {
            overview = try await repository.getProgressOverview(fromDate: nil, toDate: nil)
        } catch {
            overview = nil
            partialFailures.append("overview")
        }

        do {
            personalRecords = try await repository.getPersonalRecords(limit: 10, exerciseId: nil, metric: nil).items
        } catch {
            personalRecords = []
            partialFailures.append("records")
        }

        do {
            weeklyReport = try await repository.getWeeklyReport(weekStart: nil)
        } catch {
            weeklyReport = nil
            partialFailures.append("report")
        }

        if overview == nil, personalRecords.isEmpty, weeklyReport == nil {
            errorMessage = "Unable to load progress insights right now."
        } else if !partialFailures.isEmpty {
            errorMessage = "Some progress sections could not be loaded."
        }
    }
}
