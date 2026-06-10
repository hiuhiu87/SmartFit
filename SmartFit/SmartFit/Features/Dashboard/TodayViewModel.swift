import Combine
import Foundation

private let sleepHealthDataPreferenceKey = "smartfit.includeSleepHealthData"

@MainActor
final class TodayViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var isSyncingHealth = false
    @Published var errorMessage: String?
    @Published var readiness: ReadinessResponse?
    @Published var healthPermissionState: HealthPermissionState = .notDetermined
    @Published var includeSleepHealthData = UserDefaults.standard.bool(forKey: sleepHealthDataPreferenceKey) {
        didSet {
            UserDefaults.standard.set(includeSleepHealthData, forKey: sleepHealthDataPreferenceKey)
        }
    }
    @Published var showManualCheckIn = false
    @Published var lastSyncDate: Date?
    @Published var navigateToWorkoutBuilder = false
    @Published var activeProgram: ActiveProgramResponse?
    @Published var todayProgramWorkout: TodayProgramWorkoutResponse?
    @Published var generatedProgramWorkout: WorkoutPlanResponse?
    @Published var isGeneratingProgramWorkout = false
    @Published var navigateToCreateProgram = false
    @Published var navigateToProgramDetail = false

    private var appState: AppState?
    private var healthRepository: HealthRepository?
    private var readinessRepository: ReadinessRepository?
    private var healthKitManager: HealthKitManager?
    private var healthSummaryBuilder: HealthSummaryBuilder?
    private var programRepository: ProgramRepositoryProtocol?
    private var workoutRepository: WorkoutRepository?
    private var hasLoadedInitialData = false

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
        self.programRepository = appState.environment.programRepository
        self.workoutRepository = appState.environment.workoutRepository
        self.healthPermissionState = appState.environment.healthKitManager.currentPermissionState()
    }

    func onAppear() async {
        guard !hasLoadedInitialData, !isLoading else { return }
        hasLoadedInitialData = true
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
            if error.isCancellation { return }
            self.healthPermissionState = healthKitManager.currentPermissionState()
            if healthPermissionState == .authorized {
                await syncHealthAndCalculateReadiness()
            } else {
                self.showManualCheckIn = true
                self.errorMessage = nil
            }
        }
        await refreshProgram()
    }

    func connectHealthKit(includeSleep: Bool? = nil) async {
        guard let healthKitManager else { return }
        isSyncingHealth = true
        errorMessage = nil
        defer { isSyncingHealth = false }

        let shouldIncludeSleep = includeSleep ?? includeSleepHealthData
        includeSleepHealthData = shouldIncludeSleep
        do {
            try await healthKitManager.requestAuthorization(includeSleep: shouldIncludeSleep)
            healthPermissionState = healthKitManager.currentPermissionState()
            await syncHealthAndCalculateReadiness()
        } catch {
            if error.isCancellation { return }
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
            let summaryDraft = try await healthKitManager.fetchDailyHealthSummary(
                for: Date(),
                includeSleep: includeSleepHealthData
            )
            let request = healthSummaryBuilder.buildRequest(from: summaryDraft)
            try await healthRepository.saveHealthSummary(request)
            let readiness = try await readinessRepository.calculateReadiness(date: request.date)
            self.readiness = readiness
            self.lastSyncDate = Date()
            self.showManualCheckIn = false
        } catch {
            if error.isCancellation { return }
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
            if error.isCancellation { return }
            self.errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to calculate readiness."
        }
    }

    func programCreated(_ program: CreateProgramResponse) {
        Task { await refreshProgram() }
    }

    func refreshProgram() async {
        guard let programRepository else { return }

        do {
            let program = try await programRepository.getActiveProgram()
            activeProgram = program
            guard program != nil else {
                todayProgramWorkout = nil
                return
            }
            todayProgramWorkout = try await programRepository.getTodayProgramWorkout()
        } catch {
            if error.isCancellation { return }
            if errorMessage == nil {
                errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to load training program."
            }
        }
    }

    func openTodayWorkout() async {
        guard let programRepository, let todayProgramWorkout = todayProgramWorkout else { return }
        
        isGeneratingProgramWorkout = true
        errorMessage = nil
        defer { isGeneratingProgramWorkout = false }

        do {
            if let planId = todayProgramWorkout.scheduledWorkout?.plannedWorkoutPlanId {
                generatedProgramWorkout = try await programRepository.getWorkoutDetail(workoutId: planId)
            } else if let fallbackId = todayProgramWorkout.workoutPlanId {
                generatedProgramWorkout = try await programRepository.getWorkoutDetail(workoutId: fallbackId)
            } else {
                errorMessage = "No planned workout has been pre-generated for today."
            }
        } catch {
            if error.isCancellation { return }
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to prepare today's workout."
        }
    }

    func adjustTodayWorkout() async {
        guard let programRepository,
              let todayProgramWorkout = todayProgramWorkout,
              let scheduled = todayProgramWorkout.scheduledWorkout else { return }

        isGeneratingProgramWorkout = true
        errorMessage = nil
        defer { isGeneratingProgramWorkout = false }

        do {
            let isLowReadiness = readiness?.category == "low" || readiness?.category == "very_low"
            let adjustmentType = isLowReadiness ? "recovery_substitution" : "reduced_volume"
            let reason = todayProgramWorkout.recommendation?.message ?? "Readiness adjustment"
            
            let adjustedPlan = try await programRepository.adjustTodayWorkout(
                instanceId: scheduled.instanceId,
                adjustmentType: adjustmentType,
                reason: reason
            )
            generatedProgramWorkout = adjustedPlan
        } catch {
            if error.isCancellation { return }
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to adjust today's workout."
        }
    }

    func skipTodayWorkout() async {
        guard let programRepository,
              let todayProgramWorkout = todayProgramWorkout,
              let scheduled = todayProgramWorkout.scheduledWorkout else { return }

        isGeneratingProgramWorkout = true
        errorMessage = nil
        defer { isGeneratingProgramWorkout = false }

        do {
            try await programRepository.skipProgramWorkout(instanceId: scheduled.instanceId)
            await refreshProgram()
        } catch {
            if error.isCancellation { return }
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to skip today's workout."
        }
    }

    func rescheduleTodayWorkout(to newDate: Date) async {
        guard let programRepository,
              let todayProgramWorkout = todayProgramWorkout,
              let scheduled = todayProgramWorkout.scheduledWorkout else { return }

        isGeneratingProgramWorkout = true
        errorMessage = nil
        defer { isGeneratingProgramWorkout = false }

        do {
            let dateString = ISO8601DateFormatter.smartFitDate.string(from: newDate)
            try await programRepository.rescheduleProgramWorkout(
                instanceId: scheduled.instanceId,
                newDate: dateString
            )
            await refreshProgram()
        } catch {
            if error.isCancellation { return }
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to reschedule today's workout."
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
