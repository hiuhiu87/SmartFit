import SwiftUI

struct WorkoutPreviewView: View {
    @StateObject private var viewModel: WorkoutPreviewViewModel
    private let workoutRepository: WorkoutRepository
    private let workoutMetricsReader: HealthKitWorkoutMetricsReader?
    private let allowsRegeneration: Bool

    private let workoutDate: String
    private let readiness: ReadinessResponse?
    private let initialEquipment: [String]
    private let initialWorkoutSplit: String
    private let initialFocusMuscle: String?
    private let initialAvailableTimeMinutes: Int
    private let initialGenerationMode: String
    private let initialAvoidExercisesText: String
    private let initialUserNote: String
    
    // Program fields
    private let isProgramWorkout: Bool
    private let programWeek: Int?
    private let programDay: Int?

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
        allowsRegeneration: Bool = true,
        workoutMetricsReader: HealthKitWorkoutMetricsReader? = nil,
        isProgramWorkout: Bool = false,
        programWeek: Int? = nil,
        programDay: Int? = nil
    ) {
        self.workoutRepository = workoutRepository
        self.workoutMetricsReader = workoutMetricsReader
        self.allowsRegeneration = allowsRegeneration
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
        self.isProgramWorkout = isProgramWorkout
        self.programWeek = programWeek
        self.programDay = programDay
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.xl) {
                summaryCard

                if let reasoning = viewModel.workout.aiReasoningSummary, !reasoning.isEmpty {
                    infoCard(title: "Reasoning", message: reasoning)
                }

                if let safetyNote = viewModel.workout.safetyNote, !safetyNote.isEmpty {
                    infoCard(title: "Safety Note", message: safetyNote)
                }

                VStack(alignment: .leading, spacing: AppSpacing.md) {
                    SectionHeader(title: "Exercises")

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

                if allowsRegeneration && !isProgramWorkout {
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
                        SecondaryButton(title: "Regenerate", systemImage: "arrow.clockwise") {}
                            .allowsHitTesting(false)
                    }
                }
            }
            .padding(AppSpacing.xxl)
            .padding(.bottom, AppSpacing.huge + AppSpacing.huge + AppSpacing.sm)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle(isProgramWorkout ? "Program Workout" : "Workout Preview")
        .navigationBarTitleDisplayMode(.inline)
        .safeAreaInset(edge: .bottom) {
            VStack(spacing: 0) {
                Divider().overlay(AppColors.border)
                PrimaryButton(title: "Start Workout", systemImage: "play.fill") {
                    viewModel.startWorkout()
                }
                .padding(AppSpacing.lg)
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
        HeroCard {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: AppSpacing.sm) {
                        if isProgramWorkout {
                            Text("PROGRAM WORKOUT")
                                .font(AppTypography.caption.weight(.semibold))
                                .foregroundStyle(AppColors.primary)
                        }
                        
                        Text(viewModel.workout.title)
                            .font(AppTypography.hero)
                            .multilineTextAlignment(.leading)
                        
                        if isProgramWorkout, let week = programWeek, let day = programDay {
                            Text("Week \(week) · Day \(day)")
                                .font(AppTypography.body.weight(.semibold))
                                .foregroundStyle(AppColors.textSecondary)
                        } else {
                            StatusBadge(title: viewModel.workout.sourceBadgeTitle, color: sourceBadgeColor)
                        }
                    }
                    Spacer()
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: AppSpacing.md) {
                    MetricCard(title: "Duration", value: "\(viewModel.workout.estimatedDurationMinutes ?? initialAvailableTimeMinutes) min")
                    MetricCard(
                        title: "Focus",
                        value: viewModel.workout.focusMuscle?.replacingOccurrences(of: "_", with: " ").capitalized ?? "AI choice",
                        tint: AppColors.info
                    )
                    MetricCard(
                        title: "Split",
                        value: initialWorkoutSplit.replacingOccurrences(of: "_", with: " ").capitalized,
                        tint: AppColors.secondary
                    )
                    MetricCard(title: "Plan", value: viewModel.workout.trainingDecisionLabel, tint: AppColors.success)
                }
            }
        }
    }

    private func infoCard(title: String, message: String) -> some View {
        AppCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text(title)
                    .font(AppTypography.title)
                Text(message)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)
            }
        }
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

struct WorkoutPreviewView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack {
            WorkoutPreviewView(
                workout: .preview,
                workoutRepository: AppEnvironment.bootstrap().workoutRepository,
                workoutDate: "2026-06-10",
                readiness: nil,
                initialEquipment: ["dumbbells", "bench"],
                initialWorkoutSplit: "upper_body",
                initialFocusMuscle: "chest",
                initialAvailableTimeMinutes: 45,
                initialGenerationMode: "auto",
                initialAvoidExercisesText: "",
                initialUserNote: "",
                allowsRegeneration: true
            )
        }
        .preferredColorScheme(.dark)
        .previewDisplayName("WorkoutPreview Reference")
    }
}

private extension WorkoutPlanResponse {
    static let preview = WorkoutPlanResponse(
        workoutID: "preview-workout",
        workoutLogID: nil,
        title: "Upper Strength Builder",
        goal: "Build strength with controlled volume",
        focusMuscle: "chest",
        estimatedDurationMinutes: 45,
        trainingDecision: "normal_volume",
        aiReasoningSummary: "Readiness supports a focused upper-body session with moderate volume and clean rest periods.",
        safetyNote: "Stop if shoulder discomfort increases.",
        status: "planned",
        source: "ai",
        exercises: [
            WorkoutExerciseResponse(
                workoutPlanExerciseID: "preview-exercise-1",
                exerciseID: "bench-press",
                name: "Dumbbell Bench Press",
                orderIndex: 1,
                primaryMuscle: "chest",
                equipment: "dumbbells",
                targetSets: 4,
                targetReps: "8-10",
                targetWeight: nil,
                restSeconds: 90,
                targetRpe: 8,
                notes: "Keep two reps in reserve.",
                loggedSets: nil
            ),
            WorkoutExerciseResponse(
                workoutPlanExerciseID: "preview-exercise-2",
                exerciseID: "row",
                name: "One-Arm Dumbbell Row",
                orderIndex: 2,
                primaryMuscle: "back",
                equipment: "dumbbells",
                targetSets: 3,
                targetReps: "10-12",
                targetWeight: nil,
                restSeconds: 75,
                targetRpe: 7,
                notes: nil,
                loggedSets: nil
            )
        ]
    )
}
