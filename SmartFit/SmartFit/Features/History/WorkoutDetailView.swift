import Combine
import SwiftUI

struct WorkoutDetailView: View {
    @StateObject private var viewModel: WorkoutDetailViewModel

    init(workoutId: String, repository: HistoryRepositoryProtocol, historyItem: WorkoutHistoryItem? = nil) {
        _viewModel = StateObject(
            wrappedValue: WorkoutDetailViewModel(
                workoutId: workoutId,
                repository: repository,
                historyItem: historyItem
            )
        )
    }

    var body: some View {
        Group {
            if viewModel.isLoading && viewModel.workout == nil {
                LoadingView(message: "Loading workout detail...")
            } else if let workout = viewModel.workout {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        headerCard(for: workout)

                        ForEach(workout.exercises) { exercise in
                            AppCard(cornerRadius: 20, padding: 18) {
                                VStack(alignment: .leading, spacing: 12) {
                                    Text(exercise.name)
                                        .font(AppTypography.title)
                                    Text("\(exercise.primaryMuscle.capitalized) • \(exercise.equipment.replacingOccurrences(of: "_", with: " ").capitalized)")
                                        .font(AppTypography.caption)
                                        .foregroundStyle(AppColors.textSecondary)
                                    Text("\(exercise.targetSets) sets • \(exercise.targetReps)")
                                        .font(AppTypography.body.weight(.semibold))
                                    HStack(spacing: 12) {
                                        if let rest = exercise.restSeconds {
                                            metricPill("Rest \(rest)s")
                                        }
                                        if let rpe = exercise.targetRpe {
                                            metricPill("RPE \(rpe)")
                                        }
                                    }
                                    if let notes = exercise.notes, !notes.isEmpty {
                                        Text(notes)
                                            .font(AppTypography.body)
                                            .foregroundStyle(AppColors.textSecondary)
                                    }

                                    Divider().overlay(AppColors.border)

                                    if let loggedSets = exercise.loggedSets, !loggedSets.isEmpty {
                                        VStack(alignment: .leading, spacing: 8) {
                                            Text("Logged Sets")
                                                .font(AppTypography.body.weight(.semibold))
                                            ForEach(loggedSets) { loggedSet in
                                                HStack {
                                                    Text("Set \(loggedSet.setNumber)")
                                                    Spacer()
                                                    Text(setValueText(loggedSet))
                                                        .foregroundStyle(AppColors.textSecondary)
                                                }
                                                .font(AppTypography.caption)
                                            }
                                        }
                                    } else {
                                        Text("No sets logged for this workout.")
                                            .font(AppTypography.caption)
                                            .foregroundStyle(AppColors.textSecondary)
                                    }
                                }
                            }
                        }
                    }
                    .padding(24)
                }
                .refreshable {
                    await viewModel.refresh()
                }
            } else {
                ErrorStateView(message: viewModel.errorMessage ?? "Unable to load workout detail.") {
                    Task { await viewModel.refresh() }
                }
            }
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Workout Detail")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.load()
        }
    }

    private func headerCard(for workout: WorkoutPlanResponse) -> some View {
        AppCard(cornerRadius: 24, padding: 22) {
            VStack(alignment: .leading, spacing: 12) {
                Text(workout.title)
                    .font(AppTypography.hero)
                Text("\(workout.status.replacingOccurrences(of: "_", with: " ").capitalized) • \(workout.sourceBadgeTitle)")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)

                HStack(spacing: 10) {
                    if let duration = workout.estimatedDurationMinutes {
                        metricPill("\(duration) min")
                    }
                    metricPill(workout.goal.replacingOccurrences(of: "_", with: " ").capitalized)
                    if let focus = workout.focusMuscle {
                        metricPill(focus.replacingOccurrences(of: "_", with: " ").capitalized)
                    }
                }

                if let totalVolume = viewModel.displayTotalVolume {
                    Text("Total Volume: \(Int(totalVolume)) kg")
                        .font(AppTypography.body.weight(.semibold))
                }
            }
        }
    }

    private func metricPill(_ title: String) -> some View {
        Text(title)
            .font(AppTypography.caption)
            .foregroundStyle(AppColors.textPrimary)
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(AppColors.surfaceElevated)
            .clipShape(Capsule())
    }

    private func setValueText(_ set: LoggedSetResponse) -> String {
        let weight = set.weight.map { String(format: "%.0f kg", $0) } ?? "-"
        let reps = set.reps.map(String.init) ?? "-"
        let rpe = set.rpe.map { "RPE \($0)" } ?? ""
        return "\(weight) x \(reps) \(rpe)".trimmingCharacters(in: .whitespaces)
    }
}

@MainActor
final class WorkoutDetailViewModel: ObservableObject {
    @Published var workout: WorkoutPlanResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    let workoutId: String
    private let repository: HistoryRepositoryProtocol
    private let historyItem: WorkoutHistoryItem?

    init(workoutId: String, repository: HistoryRepositoryProtocol, historyItem: WorkoutHistoryItem?) {
        self.workoutId = workoutId
        self.repository = repository
        self.historyItem = historyItem
    }

    var displayTotalVolume: Double? {
        if let historyVolume = historyItem?.totalVolume {
            return historyVolume
        }
        guard let workout else { return nil }
        let allLoggedSets = workout.exercises.flatMap { $0.loggedSets ?? [] }
        let completedSets = allLoggedSets.filter { $0.completed }
        let total = completedSets.reduce(0.0) { partial, set in
            let weight = set.weight ?? 0
            let reps = Double(set.reps ?? 0)
            return partial + (weight * reps)
        }
        return total > 0 ? total : nil
    }

    func load() async {
        guard workout == nil else { return }
        await refresh()
    }

    func refresh() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            workout = try await repository.getWorkoutDetail(workoutId: workoutId)
        } catch {
            if error.isCancellation { return }
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to load workout detail."
        }
    }
}

#if DEBUG
struct WorkoutDetailView_Previews: PreviewProvider {
    private final class PreviewHistoryRepository: HistoryRepositoryProtocol {
        func getWorkoutHistory(limit: Int, offset: Int, status: String?, fromDate: String?, toDate: String?) async throws -> WorkoutHistoryResponse {
            .init(items: [.mockCompleted], limit: 20, offset: 0, total: 1)
        }

        func getWorkoutDetail(workoutId: String) async throws -> WorkoutPlanResponse {
            .mockAI
        }
    }

    static var previews: some View {
        NavigationStack {
            WorkoutDetailView(
                workoutId: WorkoutPlanResponse.mockAI.workoutID,
                repository: PreviewHistoryRepository(),
                historyItem: .mockCompleted
            )
        }
        .preferredColorScheme(.dark)
    }
}
#endif
