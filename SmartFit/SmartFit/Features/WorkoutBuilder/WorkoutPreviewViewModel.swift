import Combine
import Foundation

@MainActor
final class WorkoutPreviewViewModel: ObservableObject {
    @Published var workout: WorkoutPlanResponse
    @Published var isRefreshing = false
    @Published var errorMessage: String?
    @Published var navigateToActiveWorkout = false

    private let workoutRepository: WorkoutRepository

    init(workout: WorkoutPlanResponse, workoutRepository: WorkoutRepository) {
        self.workout = workout
        self.workoutRepository = workoutRepository
    }

    func refreshWorkout() async {
        isRefreshing = true
        errorMessage = nil
        defer { isRefreshing = false }

        do {
            workout = try await workoutRepository.getWorkoutDetail(workoutId: workout.workoutID)
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to refresh workout."
        }
    }

    func startWorkout() {
        navigateToActiveWorkout = true
    }
}
