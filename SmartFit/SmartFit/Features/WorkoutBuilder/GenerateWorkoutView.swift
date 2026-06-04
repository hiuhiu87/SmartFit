import SwiftUI

struct GenerateWorkoutView: View {
    @StateObject private var viewModel: GenerateWorkoutViewModel
    private let workoutRepository: WorkoutRepository
    private let workoutMetricsReader: HealthKitWorkoutMetricsReader?

    private let splitOptions: [(String, String, String)] = [
        ("full_body", "Full Body", "Balanced session"),
        ("upper_body", "Upper Body", "Chest, back, shoulders, arms"),
        ("lower_body", "Lower Body", "Legs and core"),
        ("push", "Push", "Chest, shoulders, triceps"),
        ("pull", "Pull", "Back, biceps, posterior chain"),
    ]

    private let focusOptions: [(String?, String, String)] = [
        ("let_ai_choose", "Let AI choose", "Use readiness and equipment to decide"),
        ("chest", "Chest", "Push focus"),
        ("back", "Back", "Pull focus"),
        ("legs", "Legs", "Lower body"),
        ("shoulders", "Shoulders", "Delts and support"),
        ("arms", "Arms", "Biceps and triceps"),
        ("core", "Core", "Trunk stability"),
        ("full_body", "Full Body", "Balanced session"),
    ]

    private let timeOptions = [30, 45, 60, 90]
    private let equipmentOptions = [
        "dumbbell",
        "barbell",
        "bench",
        "cable_machine",
        "smith_machine",
        "machine",
        "pull_up_bar",
        "resistance_band",
        "treadmill",
        "bodyweight",
    ]

    init(
        workoutDate: String,
        readiness: ReadinessResponse?,
        initialEquipment: [String],
        initialWorkoutSplit: String = "full_body",
        initialFocusMuscle: String? = "let_ai_choose",
        initialAvailableTimeMinutes: Int = 60,
        initialGenerationMode: String = "auto",
        initialAvoidExercisesText: String = "",
        initialUserNote: String = "",
        workoutRepository: WorkoutRepository,
        workoutMetricsReader: HealthKitWorkoutMetricsReader? = nil
    ) {
        self.workoutRepository = workoutRepository
        self.workoutMetricsReader = workoutMetricsReader
        _viewModel = StateObject(
            wrappedValue: GenerateWorkoutViewModel(
                workoutDate: workoutDate,
                readiness: readiness,
                initialEquipment: initialEquipment,
                initialWorkoutSplit: initialWorkoutSplit,
                initialFocusMuscle: initialFocusMuscle,
                initialAvailableTimeMinutes: initialAvailableTimeMinutes,
                initialGenerationMode: initialGenerationMode,
                initialAvoidExercisesText: initialAvoidExercisesText,
                initialUserNote: initialUserNote,
                workoutRepository: workoutRepository
            )
        )
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                header
                splitSection
                focusSection
                timeSection
                EquipmentSelectorView(selection: $viewModel.selectedEquipment, options: equipmentOptions)
                GenerationModePicker(selection: $viewModel.generationMode)
                textSection(
                    title: "Avoid exercises",
                    placeholder: "Anything you want to avoid today?",
                    text: $viewModel.avoidExercisesText
                )
                textSection(
                    title: "User note",
                    placeholder: "How are you feeling today?",
                    text: $viewModel.userNote
                )

                if let errorMessage = viewModel.errorMessage {
                    ErrorStateView(message: errorMessage, retryTitle: "Try Again") {
                        Task { await viewModel.generateWorkout() }
                    }
                    .frame(height: 220)
                }

                PrimaryButton(title: "Generate Workout", isLoading: viewModel.isLoading) {
                    Task { await viewModel.generateWorkout() }
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Build Today’s Workout")
        .navigationBarTitleDisplayMode(.inline)
        .navigationDestination(item: $viewModel.generatedWorkout) { workout in
            WorkoutPreviewView(
                workout: workout,
                workoutRepository: workoutRepository,
                workoutDate: viewModel.workoutDate,
                readiness: viewModel.readiness,
                initialEquipment: Array(viewModel.selectedEquipment),
                initialWorkoutSplit: viewModel.selectedWorkoutSplit,
                initialFocusMuscle: viewModel.selectedFocusMuscle,
                initialAvailableTimeMinutes: viewModel.availableTimeMinutes,
                initialGenerationMode: viewModel.generationMode,
                initialAvoidExercisesText: viewModel.avoidExercisesText,
                initialUserNote: viewModel.userNote,
                workoutMetricsReader: workoutMetricsReader
            )
        }
    }

    private var header: some View {
        AppCard(cornerRadius: 24, padding: 20) {
            VStack(alignment: .leading, spacing: 10) {
                Text("Build Today’s Workout")
                    .font(AppTypography.hero)
                Text("Adjust a few inputs, then let SmartFit build a session around your readiness.")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)

                if let readiness = viewModel.readiness {
                    HStack(spacing: 12) {
                        labelPill("Score \(readiness.displayScore)%")
                        labelPill(readiness.category.replacingOccurrences(of: "_", with: " ").capitalized)
                        labelPill(readiness.recommendation.replacingOccurrences(of: "_", with: " ").capitalized)
                    }
                }
            }
        }
    }

    private var splitSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Workout split")
                .font(AppTypography.title)

            ForEach(splitOptions, id: \.0) { option in
                SelectableCard(
                    title: option.1,
                    subtitle: option.2,
                    isSelected: viewModel.selectedWorkoutSplit == option.0,
                    action: { viewModel.selectedWorkoutSplit = option.0 }
                )
            }
        }
    }

    private var focusSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Focus muscle")
                .font(AppTypography.title)

            ForEach(focusOptions, id: \.1) { option in
                SelectableCard(
                    title: option.1,
                    subtitle: option.2,
                    isSelected: viewModel.selectedFocusMuscle == option.0,
                    action: { viewModel.selectedFocusMuscle = option.0 }
                )
            }
        }
    }

    private var timeSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Available time")
                .font(AppTypography.title)

            HStack(spacing: 12) {
                ForEach(timeOptions, id: \.self) { time in
                    Button {
                        viewModel.availableTimeMinutes = time
                    } label: {
                        Text("\(time) min")
                            .font(AppTypography.body.weight(.semibold))
                            .foregroundStyle(viewModel.availableTimeMinutes == time ? AppColors.textInverse : AppColors.textPrimary)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(viewModel.availableTimeMinutes == time ? AppColors.primary : AppColors.surfaceElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16, style: .continuous)
                                    .stroke(viewModel.availableTimeMinutes == time ? AppColors.primary : AppColors.border, lineWidth: 1)
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private func textSection(title: String, placeholder: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(AppTypography.title)

            AppInputField(cornerRadius: 16) {
                TextField(placeholder, text: text, axis: .vertical)
                    .lineLimit(3, reservesSpace: true)
                    .font(AppTypography.body)
            }
        }
    }

    private func labelPill(_ title: String) -> some View {
        Text(title)
            .font(AppTypography.caption)
            .foregroundStyle(AppColors.textPrimary)
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(AppColors.surfaceElevated)
            .clipShape(Capsule())
    }
}

#if DEBUG
struct GenerateWorkoutView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack {
            GenerateWorkoutView(
                workoutDate: "2026-06-01",
                readiness: .mockLow,
                initialEquipment: ["dumbbell", "bench", "bodyweight"],
                workoutRepository: AppEnvironment.bootstrap().workoutRepository
            )
        }
        .preferredColorScheme(.dark)
    }
}
#endif
