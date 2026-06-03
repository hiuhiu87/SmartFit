import SwiftUI

struct ActiveWorkoutView: View {
    @StateObject private var viewModel: ActiveWorkoutViewModel
    @State private var completionDifficultyFeedback: String?
    @State private var completionEnergyAfter: Int?
    @State private var completionDurationMinutes: Int?
    private let autoStartOnAppear: Bool

    init(
        workout: WorkoutPlanResponse,
        workoutRepository: WorkoutRepository,
        autoStartOnAppear: Bool = true
    ) {
        _viewModel = StateObject(
            wrappedValue: ActiveWorkoutViewModel(
                workout: workout,
                workoutRepository: workoutRepository
            )
        )
        self.autoStartOnAppear = autoStartOnAppear
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                ExerciseProgressHeaderView(
                    title: viewModel.workout.title,
                    currentIndex: max(viewModel.currentExerciseIndex + 1, 1),
                    totalCount: max(viewModel.workout.exercises.count, 1)
                )

                if viewModel.isStarting && viewModel.workoutLogId == nil {
                    AppCard(cornerRadius: 20, padding: 18) {
                        HStack(spacing: 12) {
                            ProgressView()
                                .tint(AppColors.primary)
                            Text("Starting workout...")
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                    }
                }

                if let errorMessage = viewModel.errorMessage {
                    AppCard(cornerRadius: 18, padding: 16) {
                        Text(errorMessage)
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.error)
                    }
                }

                if let exercise = viewModel.currentExercise {
                    exerciseCard(exercise)

                    if viewModel.showRestTimer {
                        RestTimerView(
                            secondsRemaining: viewModel.restSecondsRemaining,
                            onSkip: viewModel.skipRest,
                            onAdd15: { viewModel.adjustRest(by: 15) },
                            onMinus15: { viewModel.adjustRest(by: -15) }
                        )
                    } else {
                        SetLoggerView(
                            weight: $viewModel.currentWeight,
                            reps: $viewModel.currentReps,
                            rpe: $viewModel.currentRPE,
                            setNumber: viewModel.currentSetNumber,
                            targetSets: exercise.targetSets,
                            targetReps: exercise.targetReps,
                            targetRpe: exercise.targetRpe,
                            isLoading: viewModel.isLoggingSet,
                            onComplete: {
                                Task { await viewModel.completeCurrentSet() }
                            }
                        )
                    }

                    HStack(spacing: 12) {
                        SecondaryButton(title: "Previous", systemImage: "chevron.left") {
                            viewModel.goToPreviousExercise()
                        }
                        .opacity(viewModel.canGoToPreviousExercise ? 1 : 0.45)
                        .disabled(!viewModel.canGoToPreviousExercise)

                        SecondaryButton(title: "Skip", systemImage: "forward.fill") {
                            viewModel.skipCurrentExercise()
                        }
                    }

                    HStack(spacing: 12) {
                        SecondaryButton(title: "Replace", systemImage: "arrow.triangle.2.circlepath") {
                            viewModel.openReplaceExercise()
                        }
                        SecondaryButton(title: "End", systemImage: "stop.fill") {
                            viewModel.showCompleteWorkoutSheet = true
                        }
                    }
                } else {
                    ErrorStateView(message: "No exercises available in this workout.")
                        .frame(height: 260)
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Active Workout")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            guard autoStartOnAppear else { return }
            await viewModel.startWorkoutIfNeeded()
        }
        .sheet(isPresented: $viewModel.showCompleteWorkoutSheet) {
            CompleteWorkoutView(isLoading: viewModel.isCompleting) { difficultyFeedback, energyAfter, notes in
                completionDifficultyFeedback = difficultyFeedback
                completionEnergyAfter = energyAfter
                completionDurationMinutes = viewModel.workoutStartedAt.map { max(Int(Date().timeIntervalSince($0) / 60), 1) }
                Task {
                    await viewModel.completeWorkout(
                        difficultyFeedback: difficultyFeedback,
                        energyAfter: energyAfter,
                        notes: notes
                    )
                }
            }
        }
        .sheet(isPresented: $viewModel.showReplaceExerciseSheet) {
            if let exercise = viewModel.currentExercise {
                ReplaceExerciseSheet(
                    currentExercise: exercise,
                    selectedReason: $viewModel.selectedReplacementReason,
                    selectedEquipment: $viewModel.selectedReplacementEquipment,
                    userNote: $viewModel.replacementUserNote,
                    equipmentOptions: viewModel.replacementEquipmentOptions,
                    replacementOptions: viewModel.replacementOptions,
                    safetyNote: viewModel.replacementSafetyNote,
                    errorMessage: viewModel.replacementErrorMessage,
                    isFindingReplacement: viewModel.isFindingReplacement,
                    isApplyingReplacement: viewModel.isApplyingReplacement,
                    onFindReplacement: {
                        Task {
                            await viewModel.suggestReplacement(
                                reason: viewModel.selectedReplacementReason,
                                equipment: Array(viewModel.selectedReplacementEquipment).sorted(),
                                userNote: viewModel.replacementUserNote
                            )
                        }
                    },
                    onApplyReplacement: { option in
                        Task {
                            await viewModel.applyReplacement(option)
                        }
                    }
                )
            }
        }
        .navigationDestination(isPresented: Binding(
            get: { viewModel.completedResponse != nil },
            set: { isPresented in
                if !isPresented {
                    viewModel.completedResponse = nil
                }
            }
        )) {
            if let completedResponse = viewModel.completedResponse {
                WorkoutSummaryView(
                    workout: viewModel.workout,
                    completion: completedResponse,
                    difficultyFeedback: completionDifficultyFeedback,
                    energyAfter: completionEnergyAfter,
                    durationMinutes: completionDurationMinutes
                )
            }
        }
    }

    private func exerciseCard(_ exercise: WorkoutExerciseResponse) -> some View {
        AppCard(cornerRadius: 24, padding: 20) {
            VStack(alignment: .leading, spacing: 16) {
                Text(exercise.name)
                    .font(AppTypography.hero)
                    .lineLimit(2)
                    .minimumScaleFactor(0.75)

                HStack(spacing: 8) {
                    StatusBadge(title: exercise.primaryMuscle.replacingOccurrences(of: "_", with: " ").capitalized)
                    StatusBadge(title: exercise.equipment.replacingOccurrences(of: "_", with: " ").capitalized, color: AppColors.secondary)
                }

                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 8) {
                    statBox("Sets", "\(exercise.targetSets)")
                    statBox("Reps", exercise.targetReps)
                    statBox("Rest", exercise.restSeconds.map { "\($0)s" } ?? "Free")
                    statBox("RPE", exercise.targetRpe.map(String.init) ?? "-")
                }

                if let notes = exercise.notes, !notes.isEmpty {
                    Text(notes)
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textSecondary)
                }
            }
        }
    }

    private func statBox(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
            Text(value)
                .font(AppTypography.body.weight(.semibold))
                .lineLimit(1)
                .minimumScaleFactor(0.7)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(AppColors.surfaceElevated)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

#if DEBUG
struct ActiveWorkoutView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack {
            ActiveWorkoutView(
                workout: .mockAI,
                workoutRepository: AppEnvironment.bootstrap().workoutRepository,
                autoStartOnAppear: false
            )
        }
        .preferredColorScheme(.dark)
    }
}
#endif
