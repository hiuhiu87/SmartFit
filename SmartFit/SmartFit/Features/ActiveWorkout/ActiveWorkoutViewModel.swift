import Combine
import Foundation
import SwiftUI

@MainActor
final class ActiveWorkoutViewModel: ObservableObject {
    @Published var workout: WorkoutPlanResponse
    @Published var workoutLogId: String?
    @Published var currentExerciseIndex = 0
    @Published var currentSetNumber = 1
    @Published var currentWeight: Double?
    @Published var currentReps = 10
    @Published var currentRPE: Int?
    @Published var isStarting = false
    @Published var isLoggingSet = false
    @Published var isCompleting = false
    @Published var errorMessage: String?
    @Published var showRestTimer = false
    @Published var restSecondsRemaining = 0
    @Published var workoutStartedAt: Date?
    @Published var completedResponse: CompleteWorkoutResponse?
    @Published var showCompleteWorkoutSheet = false
    @Published var showReplaceExerciseSheet = false
    @Published var showAIChatSheet = false
    @Published var isFindingReplacement = false
    @Published var isApplyingReplacement = false
    @Published var completionStatusMessage: String?
    @Published var completionMetricsNote: String?
    @Published var replacementErrorMessage: String?
    @Published var replacementOptions: [ReplacementOptionResponse] = []
    @Published var replacementSafetyNote: String?
    @Published var selectedReplacementReason = "equipment_unavailable"
    @Published var selectedReplacementEquipment: Set<String> = ["bodyweight"]
    @Published var replacementUserNote = ""

    private let workoutRepository: WorkoutRepositoryProtocol
    private let workoutMetricsReader: HealthKitWorkoutMetricsReader?
    private var restTimerTask: Task<Void, Never>?

    init(
        workout: WorkoutPlanResponse,
        workoutRepository: WorkoutRepositoryProtocol,
        workoutMetricsReader: HealthKitWorkoutMetricsReader? = nil
    ) {
        self.workout = workout
        self.workoutRepository = workoutRepository
        self.workoutMetricsReader = workoutMetricsReader
        self.workoutLogId = workout.workoutLogID
        hydrateInputsForCurrentExercise()
    }

    deinit {
        restTimerTask?.cancel()
    }

    var currentExercise: WorkoutExerciseResponse? {
        guard workout.exercises.indices.contains(currentExerciseIndex) else { return nil }
        return workout.exercises[currentExerciseIndex]
    }

    var exerciseProgressText: String {
        "\(min(currentExerciseIndex + 1, workout.exercises.count)) of \(workout.exercises.count)"
    }

    var isOnLastExercise: Bool {
        currentExerciseIndex >= max(workout.exercises.count - 1, 0)
    }

    var canGoToPreviousExercise: Bool {
        currentExerciseIndex > 0
    }

    var shouldShowFinishWorkoutCTA: Bool {
        isOnLastExercise && currentSetNumber > (currentExercise?.targetSets ?? 1)
    }

    var replacementEquipmentOptions: [String] {
        [
            "dumbbell",
            "barbell",
            "bench",
            "cable_machine",
            "machine",
            "smith_machine",
            "pull_up_bar",
            "resistance_band",
            "treadmill",
            "bodyweight",
        ]
    }

    func startWorkoutIfNeeded() async {
        guard workoutLogId == nil else { return }
        isStarting = true
        errorMessage = nil
        defer { isStarting = false }

        do {
            let startedAt = ISO8601DateFormatter().string(from: Date())
            let response = try await workoutRepository.startWorkout(
                workoutId: workout.workoutID,
                request: StartWorkoutRequest(startedAt: startedAt)
            )
            workoutLogId = response.workoutLogID
            workoutStartedAt = Self.parseAPIDate(response.startedAt) ?? Date()
            workout = try await workoutRepository.getWorkoutDetail(workoutId: workout.workoutID)
            hydrateInputsForCurrentExercise()
        } catch {
            errorMessage = readableMessage(for: error, fallback: "Unable to start workout.")
        }
    }

    func openReplaceExercise() {
        guard currentExercise != nil else { return }
        selectedReplacementReason = Self.defaultReplacementReason
        selectedReplacementEquipment = defaultReplacementEquipment()
        replacementUserNote = ""
        replacementErrorMessage = nil
        replacementOptions = []
        replacementSafetyNote = nil
        showReplaceExerciseSheet = true
    }

    func suggestReplacement(reason: String, equipment: [String], userNote: String?) async {
        guard let exercise = currentExercise else {
            replacementErrorMessage = "No active exercise found."
            return
        }

        isFindingReplacement = true
        replacementErrorMessage = nil
        replacementOptions = []
        replacementSafetyNote = nil
        defer { isFindingReplacement = false }

        do {
            let response = try await workoutRepository.suggestReplacement(
                ReplaceExerciseRequest(
                    workoutId: workout.workoutID,
                    workoutPlanExerciseId: exercise.workoutPlanExerciseID,
                    reason: reason,
                    availableEquipment: equipment.isEmpty ? ["bodyweight"] : equipment,
                    userNote: userNote?.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty
                )
            )
            replacementOptions = response.replacementOptions
            replacementSafetyNote = response.safetyNote
            if response.replacementOptions.isEmpty {
                replacementErrorMessage = "No suitable replacement found. Try selecting more equipment or choose bodyweight."
            }
        } catch {
            replacementErrorMessage = readableMessage(for: error, fallback: "Unable to find replacement exercises.")
        }
    }

    func applyReplacement(_ option: ReplacementOptionResponse) async {
        guard let exercise = currentExercise else {
            replacementErrorMessage = "No active exercise found."
            return
        }

        let originalPlanExerciseId = exercise.workoutPlanExerciseID
        let originalOrderIndex = exercise.orderIndex
        let fallbackIndex = currentExerciseIndex

        isApplyingReplacement = true
        replacementErrorMessage = nil
        defer { isApplyingReplacement = false }

        do {
            _ = try await workoutRepository.applyReplacement(
                workoutId: workout.workoutID,
                workoutPlanExerciseId: originalPlanExerciseId,
                request: ApplyExerciseReplacementRequest(
                    replacementExerciseId: option.exerciseId,
                    targetSets: option.targetSets,
                    targetReps: option.targetReps,
                    restSeconds: option.restSeconds,
                    targetRpe: option.targetRpe,
                    reason: selectedReplacementReason
                )
            )
            let didRefresh = await refreshAfterReplacement(
                originalPlanExerciseId: originalPlanExerciseId,
                originalOrderIndex: originalOrderIndex,
                fallbackIndex: fallbackIndex
            )
            if didRefresh {
                showReplaceExerciseSheet = false
            }
        } catch {
            replacementErrorMessage = readableMessage(for: error, fallback: "Unable to apply this replacement.")
        }
    }

    func refreshAfterReplacement() async {
        _ = await refreshAfterReplacement(
            originalPlanExerciseId: currentExercise?.workoutPlanExerciseID,
            originalOrderIndex: currentExercise?.orderIndex,
            fallbackIndex: currentExerciseIndex
        )
    }

    func completeCurrentSet() async {
        guard let workoutLogId else {
            errorMessage = "Workout session is not ready yet. Try starting again."
            return
        }
        guard let exercise = currentExercise else {
            errorMessage = "No active exercise found."
            return
        }
        let loggedExerciseIndex = currentExerciseIndex
        let loggedSetNumber = currentSetNumber
        let targetSets = exercise.targetSets

        isLoggingSet = true
        errorMessage = nil
        defer { isLoggingSet = false }

        do {
            _ = try await workoutRepository.logSet(
                workoutId: workout.workoutID,
                request: LogSetRequest(
                    workoutLogId: workoutLogId,
                    workoutPlanExerciseId: exercise.workoutPlanExerciseID,
                    setNumber: loggedSetNumber,
                    weight: currentWeight,
                    reps: currentReps,
                    rpe: currentRPE,
                    completed: true
                )
            )
            await refreshWorkoutDetail()

            let restSeconds = exercise.restSeconds ?? 0
            if loggedSetNumber < targetSets {
                currentExerciseIndex = loggedExerciseIndex
                currentSetNumber = loggedSetNumber + 1
                currentWeight = currentExercise?.loggedSets?.last?.weight ?? currentWeight
                currentReps = currentExercise?.loggedSets?.last?.reps ?? currentReps
                currentRPE = currentExercise?.loggedSets?.last?.rpe ?? currentRPE
                if restSeconds > 0 {
                    startRestTimer(seconds: restSeconds)
                }
            } else if loggedExerciseIndex < workout.exercises.count - 1 {
                currentExerciseIndex = loggedExerciseIndex + 1
                hydrateInputsForCurrentExercise()
                if restSeconds > 0 {
                    startRestTimer(seconds: restSeconds)
                }
            } else {
                currentSetNumber = targetSets + 1
                showCompleteWorkoutSheet = true
            }
        } catch {
            errorMessage = readableMessage(for: error, fallback: "Unable to log set.")
        }
    }

    func skipCurrentExercise() {
        stopRestTimer()
        errorMessage = nil
        if currentExerciseIndex < workout.exercises.count - 1 {
            currentExerciseIndex += 1
            hydrateInputsForCurrentExercise()
        } else {
            showCompleteWorkoutSheet = true
        }
    }

    func goToNextExercise() {
        guard currentExerciseIndex < workout.exercises.count - 1 else { return }
        stopRestTimer()
        currentExerciseIndex += 1
        hydrateInputsForCurrentExercise()
    }

    func goToPreviousExercise() {
        guard currentExerciseIndex > 0 else { return }
        stopRestTimer()
        currentExerciseIndex -= 1
        hydrateInputsForCurrentExercise()
    }

    func startRestTimer(seconds: Int) {
        guard seconds > 0 else {
            showRestTimer = false
            return
        }
        stopRestTimer()
        restSecondsRemaining = seconds
        showRestTimer = true
        restTimerTask = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled && self.restSecondsRemaining > 0 {
                try? await Task.sleep(for: .seconds(1))
                if Task.isCancelled { return }
                self.restSecondsRemaining -= 1
            }
            if !Task.isCancelled {
                self.showRestTimer = false
            }
        }
    }

    func adjustRest(by delta: Int) {
        restSecondsRemaining = max(0, restSecondsRemaining + delta)
        if restSecondsRemaining == 0 {
            skipRest()
        }
    }

    func skipRest() {
        stopRestTimer()
    }

    func completeWorkout(
        difficultyFeedback: String,
        energyAfter: Int?,
        notes: String?
    ) async {
        guard let workoutLogId else {
            errorMessage = "Workout session is missing."
            return
        }
        isCompleting = true
        errorMessage = nil
        completionMetricsNote = nil
        defer { isCompleting = false }

        let completedAt = Date()
        let durationMinutes = workoutStartedAt.map {
            max(Int(completedAt.timeIntervalSince($0) / 60), 1)
        } ?? 1
        let startDate = workoutStartedAt ?? completedAt.addingTimeInterval(-Double(durationMinutes * 60))
        let healthMetrics = await readWorkoutMetrics(
            startDate: startDate,
            endDate: completedAt
        )

        do {
            completionStatusMessage = "Saving workout..."
            let response = try await workoutRepository.completeWorkout(
                workoutId: workout.workoutID,
                request: CompleteWorkoutRequest(
                    workoutLogId: workoutLogId,
                    completedAt: Self.apiDateFormatter.string(from: completedAt),
                    durationMinutes: durationMinutes,
                    caloriesBurned: healthMetrics?.activeEnergyBurned,
                    avgHeartRate: healthMetrics?.avgHeartRate,
                    // Backend currently accepts calories and average heart rate only.
                    maxHeartRate: nil,
                    minHeartRate: nil,
                    difficultyFeedback: difficultyFeedback,
                    energyAfter: energyAfter,
                    notes: notes
                )
            )
            completedResponse = response
            showCompleteWorkoutSheet = false
            await refreshWorkoutDetail()
        } catch {
            errorMessage = readableMessage(for: error, fallback: "Unable to finish workout.")
            showCompleteWorkoutSheet = true
        }
        completionStatusMessage = nil
    }

    func refreshWorkoutDetail() async {
        do {
            workout = try await workoutRepository.getWorkoutDetail(workoutId: workout.workoutID)
            if workoutLogId == nil {
                workoutLogId = workout.workoutLogID
            }
            hydrateInputsForCurrentExercise()
        } catch {
            errorMessage = readableMessage(for: error, fallback: "Unable to refresh workout.")
        }
    }

    private func refreshAfterReplacement(
        originalPlanExerciseId: String?,
        originalOrderIndex: Int?,
        fallbackIndex: Int
    ) async -> Bool {
        do {
            let refreshedWorkout = try await workoutRepository.getWorkoutDetail(workoutId: workout.workoutID)
            workout = refreshedWorkout
            if workoutLogId == nil {
                workoutLogId = refreshedWorkout.workoutLogID
            }

            if
                let originalPlanExerciseId,
                let matchingIndex = refreshedWorkout.exercises.firstIndex(where: { $0.workoutPlanExerciseID == originalPlanExerciseId })
            {
                currentExerciseIndex = matchingIndex
            } else if
                let originalOrderIndex,
                let matchingIndex = refreshedWorkout.exercises.firstIndex(where: { $0.orderIndex == originalOrderIndex })
            {
                currentExerciseIndex = matchingIndex
            } else {
                currentExerciseIndex = min(fallbackIndex, max(refreshedWorkout.exercises.count - 1, 0))
            }

            hydrateInputsForCurrentExercise()
            return true
        } catch {
            replacementErrorMessage = readableMessage(for: error, fallback: "Replacement applied, but workout refresh failed.")
            return false
        }
    }

    private func hydrateInputsForCurrentExercise() {
        guard let exercise = currentExercise else { return }
        let completedSets = (exercise.loggedSets ?? []).filter { $0.completed }
        currentSetNumber = min(completedSets.count + 1, max(exercise.targetSets, 1))
        currentWeight = completedSets.last?.weight
        currentReps = completedSets.last?.reps ?? exercise.suggestedDefaultReps
        currentRPE = completedSets.last?.rpe ?? exercise.suggestedDefaultRPE
    }

    private func stopRestTimer() {
        restTimerTask?.cancel()
        restTimerTask = nil
        restSecondsRemaining = 0
        showRestTimer = false
    }

    private func readWorkoutMetrics(
        startDate: Date,
        endDate: Date
    ) async -> WorkoutHealthMetrics? {
        guard let workoutMetricsReader else { return nil }
        completionStatusMessage = "Syncing workout metrics..."
        do {
            let metrics = try await withWorkoutMetricsTimeout(seconds: 2) {
                try await workoutMetricsReader.readMetrics(
                    startDate: startDate,
                    endDate: endDate
                )
            }
            guard metrics.hasSendableMetrics else {
                completionMetricsNote = "Health metrics were not available."
                return nil
            }
            return metrics
        } catch {
            completionMetricsNote = "Health metrics were not available."
            return nil
        }
    }

    private func withWorkoutMetricsTimeout<T>(
        seconds: UInt64,
        operation: @escaping () async throws -> T
    ) async throws -> T {
        try await withThrowingTaskGroup(of: T.self) { group in
            group.addTask {
                try await operation()
            }
            group.addTask {
                try await Task.sleep(nanoseconds: seconds * 1_000_000_000)
                throw HealthKitError.noData
            }

            guard let result = try await group.next() else {
                throw HealthKitError.noData
            }
            group.cancelAll()
            return result
        }
    }

    private func readableMessage(for error: Error, fallback: String) -> String {
        if let apiError = error as? APIError {
            switch apiError {
            case .server(_, let message):
                return message
            case .transport:
                return "Network error. Please try again."
            case .decodingError:
                return "Received an unexpected response from the server."
            case .unauthorized:
                return "Your session expired. Please log in again."
            default:
                return fallback
            }
        }
        return (error as? LocalizedError)?.errorDescription ?? fallback
    }

    private func defaultReplacementEquipment() -> Set<String> {
        let workoutEquipment = Set(workout.exercises.map(\.equipment))
        let selected = workoutEquipment.isEmpty ? Set(["bodyweight", "dumbbell", "bench"]) : workoutEquipment
        return selected.union(["bodyweight"])
    }

    private static let apiDateFormatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()

    private static let apiDateFormatterNoFraction: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()

    private static func parseAPIDate(_ value: String?) -> Date? {
        guard let value else { return nil }
        return apiDateFormatter.date(from: value) ?? apiDateFormatterNoFraction.date(from: value)
    }

    private static let defaultReplacementReason = "equipment_unavailable"
}

private extension String {
    var nilIfEmpty: String? {
        isEmpty ? nil : self
    }
}
