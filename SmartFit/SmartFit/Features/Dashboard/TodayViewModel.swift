import Combine
import Foundation

@MainActor
final class TodayViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var isSyncingHealth = false
    @Published var errorMessage: String?
    @Published var readiness: ReadinessResponse?
    @Published var healthPermissionState: HealthPermissionState = .notDetermined
    @Published var showManualCheckIn = false
    @Published var lastSyncDate: Date?
    @Published var navigateToWorkoutBuilder = false

    private var appState: AppState?
    private var healthRepository: HealthRepository?
    private var readinessRepository: ReadinessRepository?
    private var healthKitManager: HealthKitManager?
    private var healthSummaryBuilder: HealthSummaryBuilder?

    var workoutDate: String {
        readiness?.date ?? HealthSummaryBuilder().dateString(for: Date())
    }

    func configure(appState: AppState) {
        if self.appState === appState { return }
        self.appState = appState
        self.healthRepository = appState.environment.healthRepository
        self.readinessRepository = appState.environment.readinessRepository
        self.healthKitManager = appState.environment.healthKitManager
        self.healthSummaryBuilder = appState.environment.healthSummaryBuilder
        self.healthPermissionState = appState.environment.healthKitManager.currentPermissionState()
    }

    func onAppear() async {
        guard readiness == nil, !isLoading else { return }
        await refresh()
    }

    func refresh() async {
        guard let readinessRepository, let healthKitManager else { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let readiness = try await readinessRepository.getTodayReadiness()
            self.readiness = readiness
            self.healthPermissionState = healthKitManager.currentPermissionState()
            self.showManualCheckIn = false
        } catch {
            self.readiness = nil
            self.healthPermissionState = healthKitManager.currentPermissionState()
            if healthPermissionState == .authorized {
                await syncHealthAndCalculateReadiness()
            } else {
                self.showManualCheckIn = true
                self.errorMessage = nil
            }
        }
    }

    func connectHealthKit() async {
        guard let healthKitManager else { return }
        isSyncingHealth = true
        errorMessage = nil
        defer { isSyncingHealth = false }

        do {
            try await healthKitManager.requestAuthorization()
            healthPermissionState = healthKitManager.currentPermissionState()
            await syncHealthAndCalculateReadiness()
        } catch {
            healthPermissionState = healthKitManager.currentPermissionState()
            showManualCheckIn = true
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to connect Apple Health."
        }
    }

    func syncHealthAndCalculateReadiness() async {
        guard let healthRepository,
              let readinessRepository,
              let healthKitManager,
              let healthSummaryBuilder else { return }

        isSyncingHealth = true
        errorMessage = nil
        defer { isSyncingHealth = false }

        do {
            let summaryDraft = try await healthKitManager.fetchDailyHealthSummary(for: Date())
            let request = healthSummaryBuilder.buildRequest(from: summaryDraft)
            try await healthRepository.saveHealthSummary(request)
            let readiness = try await readinessRepository.calculateReadiness(date: request.date)
            self.readiness = readiness
            self.lastSyncDate = Date()
            self.showManualCheckIn = false
        } catch {
            self.showManualCheckIn = true
            self.errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to sync health data."
        }
    }

    func submitManualCheckIn(_ submission: ManualCheckInSubmission) async {
        guard let healthRepository, let readinessRepository else { return }
        isSyncingHealth = true
        errorMessage = nil
        defer { isSyncingHealth = false }

        do {
            let request = ManualCheckInRequest(
                date: submission.date,
                energy: normalizedFivePointScale(from: submission.energyLevel),
                soreness: normalizedFivePointScale(from: submission.sorenessLevel),
                stress: normalizedFivePointScale(from: submission.stressLevel),
                motivation: normalizedFivePointScale(from: submission.energyLevel),
                sleepQuality: normalizedFivePointScale(from: Int((submission.sleepHours ?? 5).rounded())),
                notes: submission.painNote
            )
            try await healthRepository.saveManualCheckIn(request)
            let readiness = try await readinessRepository.calculateReadiness(date: submission.date)
            self.readiness = readiness
            self.showManualCheckIn = false
            self.lastSyncDate = Date()
        } catch {
            self.errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to calculate readiness."
        }
    }

    private func normalizedFivePointScale(from value: Int) -> Int {
        let clamped = min(max(value, 1), 10)
        switch clamped {
        case 1...2: return 1
        case 3...4: return 2
        case 5...6: return 3
        case 7...8: return 4
        default: return 5
        }
    }
}
