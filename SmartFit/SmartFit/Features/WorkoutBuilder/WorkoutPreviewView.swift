import SwiftUI

struct WorkoutPreviewView: View {
    @StateObject private var viewModel: WorkoutPreviewViewModel
    private let workoutRepository: WorkoutRepository
    private let workoutMetricsReader: HealthKitWorkoutMetricsReader?

    private let workoutDate: String
    private let readiness: ReadinessResponse?
    private let initialEquipment: [String]
    private let initialWorkoutSplit: String
    private let initialFocusMuscle: String?
    private let initialAvailableTimeMinutes: Int
    private let initialGenerationMode: String
    private let initialAvoidExercisesText: String
    private let initialUserNote: String

    init(
        workout: WorkoutPlanResponse,
        workoutRepository: WorkoutRepository,
        workoutDate: String,
        readiness: ReadinessResponse?,
        initialEquipment: [String],
        initialWorkoutSplit: String = "full_body",
        initialFocusMuscle: String?,
        initialAvailableTimeMinutes: Int,
        initialGenerationMode: String,
        initialAvoidExercisesText: String,
        initialUserNote: String,
        workoutMetricsReader: HealthKitWorkoutMetricsReader? = nil
    ) {
        self.workoutRepository = workoutRepository
        self.workoutMetricsReader = workoutMetricsReader
        _viewModel = StateObject(
            wrappedValue: WorkoutPreviewViewModel(
                workout: workout,
                workoutRepository: workoutRepository
            )
        )
        self.workoutDate = workoutDate
        self.readiness = readiness
        self.initialEquipment = initialEquipment
        self.initialWorkoutSplit = initialWorkoutSplit
        self.initialFocusMuscle = initialFocusMuscle
        self.initialAvailableTimeMinutes = initialAvailableTimeMinutes
        self.initialGenerationMode = initialGenerationMode
        self.initialAvoidExercisesText = initialAvoidExercisesText
        self.initialUserNote = initialUserNote
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                summaryCard

                if let reasoning = viewModel.workout.aiReasoningSummary, !reasoning.isEmpty {
                    infoCard(title: "Reasoning", message: reasoning)
                }

                if let safetyNote = viewModel.workout.safetyNote, !safetyNote.isEmpty {
                    infoCard(title: "Safety Note", message: safetyNote)
                }

                VStack(alignment: .leading, spacing: 14) {
                    Text("Exercises")
                        .font(AppTypography.title)

                    ForEach(viewModel.workout.exercises) { exercise in
                        WorkoutExerciseCard(exercise: exercise)
                    }
                }

                if let errorMessage = viewModel.errorMessage {
                    ErrorStateView(message: errorMessage, retryTitle: "Refresh") {
                        Task { await viewModel.refreshWorkout() }
                    }
                    .frame(height: 220)
                }

                VStack(spacing: 12) {
                    NavigationLink {
                        GenerateWorkoutView(
                            workoutDate: workoutDate,
                            readiness: readiness,
                            initialEquipment: initialEquipment,
                            initialWorkoutSplit: initialWorkoutSplit,
                            initialFocusMuscle: initialFocusMuscle,
                            initialAvailableTimeMinutes: initialAvailableTimeMinutes,
                            initialGenerationMode: initialGenerationMode,
                            initialAvoidExercisesText: initialAvoidExercisesText,
                            initialUserNote: initialUserNote,
                            workoutRepository: workoutRepository,
                            workoutMetricsReader: workoutMetricsReader
                        )
                    } label: {
                        Text("Regenerate")
                            .font(AppTypography.body.weight(.semibold))
                            .foregroundStyle(AppColors.textPrimary)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(AppColors.surfaceElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16, style: .continuous)
                                    .stroke(AppColors.border, lineWidth: 1)
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    }
                }
            }
            .padding(24)
            .padding(.bottom, 86)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Workout Preview")
        .navigationBarTitleDisplayMode(.inline)
        .safeAreaInset(edge: .bottom) {
            VStack(spacing: 0) {
                Divider().overlay(AppColors.border)
                PrimaryButton(title: "Start Workout", systemImage: "play.fill") {
                    viewModel.startWorkout()
                }
                .padding(16)
                .background(AppColors.background.opacity(0.96))
            }
        }
        .refreshable {
            await viewModel.refreshWorkout()
        }
        .navigationDestination(isPresented: $viewModel.navigateToActiveWorkout) {
            ActiveWorkoutView(
                workout: viewModel.workout,
                workoutRepository: workoutRepository,
                workoutMetricsReader: workoutMetricsReader
            )
        }
    }

    private var summaryCard: some View {
        AppCard(cornerRadius: 24, padding: 22) {
            VStack(alignment: .leading, spacing: 16) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(viewModel.workout.title)
                            .font(AppTypography.hero)
                        StatusBadge(title: viewModel.workout.sourceBadgeTitle, color: sourceBadgeColor)
                    }
                    Spacer()
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                    compactMetric("Duration", "\(viewModel.workout.estimatedDurationMinutes ?? initialAvailableTimeMinutes) min")
                    compactMetric("Focus", viewModel.workout.focusMuscle?.replacingOccurrences(of: "_", with: " ").capitalized ?? "AI choice")
                    compactMetric("Split", initialWorkoutSplit.replacingOccurrences(of: "_", with: " ").capitalized)
                    compactMetric("Plan", viewModel.workout.trainingDecisionLabel)
                }
            }
        }
    }

    private func infoCard(title: String, message: String) -> some View {
        AppCard(cornerRadius: 20, padding: 18) {
            VStack(alignment: .leading, spacing: 8) {
                Text(title)
                    .font(AppTypography.title)
                Text(message)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)
            }
        }
    }

    private func compactMetric(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
            Text(value)
                .font(AppTypography.body.weight(.semibold))
                .foregroundStyle(AppColors.textPrimary)
                .lineLimit(1)
                .minimumScaleFactor(0.75)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(AppColors.surfaceElevated)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var sourceBadgeColor: Color {
        switch viewModel.workout.source {
        case "ai":
            return AppColors.primary
        case "fallback":
            return AppColors.warning
        case "manual":
            return AppColors.textSecondary
        default:
            return AppColors.primary
        }
    }
}

#if DEBUG
struct WorkoutPreviewView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            NavigationStack {
                WorkoutPreviewView(
                    workout: .mockAI,
                    workoutRepository: AppEnvironment.bootstrap().workoutRepository,
                    workoutDate: "2026-06-01",
                    readiness: .mockExcellent,
                    initialEquipment: ["dumbbell", "bench", "bodyweight"],
                    initialFocusMuscle: "chest",
                    initialAvailableTimeMinutes: 60,
                    initialGenerationMode: "auto",
                    initialAvoidExercisesText: "",
                    initialUserNote: ""
                )
            }

            NavigationStack {
                WorkoutPreviewView(
                    workout: .mockFallback,
                    workoutRepository: AppEnvironment.bootstrap().workoutRepository,
                    workoutDate: "2026-06-01",
                    readiness: .mockLow,
                    initialEquipment: ["bodyweight"],
                    initialFocusMuscle: "full_body",
                    initialAvailableTimeMinutes: 45,
                    initialGenerationMode: "rule_based",
                    initialAvoidExercisesText: "",
                    initialUserNote: ""
                )
            }
        }
        .preferredColorScheme(.dark)
    }
}
#endif
