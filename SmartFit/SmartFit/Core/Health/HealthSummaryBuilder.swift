import Foundation

struct HealthSummaryBuilder {
    private let dateFormatter: DateFormatter

    init() {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = .current
        formatter.dateFormat = "yyyy-MM-dd"
        self.dateFormatter = formatter
    }

    func buildRequest(from draft: HealthSummaryDraft) -> HealthSummaryRequest {
        HealthSummaryRequest(
            date: dateFormatter.string(from: draft.date),
            sleepHours: draft.sleepHours,
            sleepEfficiency: nil,
            restingHeartRate: draft.restingHeartRate,
            heartRateVariability: draft.hrvMS,
            steps: draft.steps,
            activeEnergyKcal: draft.activeEnergyBurned
        )
    }

    func dateString(for date: Date) -> String {
        dateFormatter.string(from: date)
    }
}
