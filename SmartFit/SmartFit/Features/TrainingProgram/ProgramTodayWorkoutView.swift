import SwiftUI

struct ProgramTodayWorkoutView: View {
    let program: TrainingProgramResponse
    let todayWorkout: TodayProgramWorkoutResponse
    let readiness: ReadinessResponse?
    let equipment: [String]
    let programRepository: ProgramRepository
    let workoutRepository: WorkoutRepository
    let workoutMetricsReader: HealthKitWorkoutMetricsReader?

    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var workout: WorkoutPlanResponse?
    @State private var generatedWorkoutID: String?

    init(
        program: TrainingProgramResponse,
        todayWorkout: TodayProgramWorkoutResponse,
        readiness: ReadinessResponse?,
        equipment: [String],
        programRepository: ProgramRepository,
        workoutRepository: WorkoutRepository,
        workoutMetricsReader: HealthKitWorkoutMetricsReader?
    ) {
        self.program = program
        self.todayWorkout = todayWorkout
        self.readiness = readiness
        self.equipment = equipment
        self.programRepository = programRepository
        self.workoutRepository = workoutRepository
        self.workoutMetricsReader = workoutMetricsReader
        _generatedWorkoutID = State(initialValue: todayWorkout.workoutPlanId)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                workoutCard

                if let readiness {
                    readinessCard(readiness)
                }

                if let template = todayWorkout.template {
                    slotOverview(template)
                }

                if let errorMessage {
                    ErrorStateView(message: errorMessage, retryTitle: "Try Again") {
                        Task { await openOrGenerateWorkout() }
                    }
                    .frame(height: 220)
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Today’s Program")
        .navigationBarTitleDisplayMode(.inline)
        .safeAreaInset(edge: .bottom) {
            if todayWorkout.status != "completed" && todayWorkout.status != "skipped" {
                VStack(spacing: 0) {
                    Divider().overlay(AppColors.border)
                    PrimaryButton(
                        title: generatedWorkoutID == nil
                            ? "Generate Today’s Workout"
                            : "Open Today’s Workout",
                        isLoading: isLoading,
                        systemImage: "play.fill"
                    ) {
                        Task { await openOrGenerateWorkout() }
                    }
                    .padding(16)
                    .background(AppColors.background.opacity(0.96))
                }
            }
        }
        .navigationDestination(item: $workout) { workout in
            WorkoutPreviewView(
                workout: workout,
                workoutRepository: workoutRepository,
                workoutDate: workoutDate,
                readiness: readiness,
                initialEquipment: equipment,
                initialWorkoutSplit: todayWorkout.template?.workoutType ?? "full_body",
                initialFocusMuscle: todayWorkout.template?.focusType,
                initialAvailableTimeMinutes: todayWorkout.template?.estimatedDurationMinutes
                    ?? program.sessionDurationMinutes,
                initialGenerationMode: program.generationMode,
                initialAvoidExercisesText: "",
                initialUserNote: "",
                allowsRegeneration: false,
                workoutMetricsReader: workoutMetricsReader
            )
        }
    }

    private var workoutCard: some View {
        AppCard(cornerRadius: 24, padding: 22) {
            VStack(alignment: .leading, spacing: 14) {
                Text(
                    "WEEK \(todayWorkout.weekNumber) · "
                        + "DAY \((todayWorkout.dayIndex ?? program.currentDayIndex) + 1)"
                )
                .font(AppTypography.caption.weight(.semibold))
                .foregroundStyle(AppColors.primary)

                Text(todayWorkout.template?.title ?? "Program Rest Day")
                    .font(AppTypography.hero)

                if let template = todayWorkout.template {
                    HStack(spacing: 16) {
                        if let duration = template.estimatedDurationMinutes {
                            Label("\(duration) min", systemImage: "clock")
                        }
                        Label(template.focusType.programDisplayName, systemImage: "scope")
                    }
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
                }

                StatusBadge(
                    title: (todayWorkout.status ?? "scheduled").programDisplayName,
                    color: statusColor
                )
            }
        }
    }

    private func readinessCard(_ readiness: ReadinessResponse) -> some View {
        AppCard {
            HStack(spacing: 16) {
                Text("\(readiness.displayScore)")
                    .font(.system(size: 44, weight: .bold, design: .rounded))
                    .foregroundStyle(ReadinessStyle.color(for: readiness.category))
                VStack(alignment: .leading, spacing: 4) {
                    Text("Today’s Readiness")
                        .font(AppTypography.body.weight(.semibold))
                    Text(readiness.recommendation.programDisplayName)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }
                Spacer()
            }
        }
    }

    private func slotOverview(_ template: ProgramWorkoutTemplateSummary) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            SectionHeader(
                title: "Session Structure",
                subtitle: "Structured for \(template.focusType.programDisplayName)."
            )
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(template.title)
                        .font(AppTypography.body.weight(.semibold))
                    Text(template.focusType.programDisplayName)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }
                Spacer()
            }
            .padding(16)
            .background(AppColors.surface)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        }
    }

    private var workoutDate: String {
        readiness?.date ?? ISO8601DateFormatter.smartFitDate.string(from: Date())
    }

    private var statusColor: Color {
        switch todayWorkout.status {
        case "completed": return AppColors.success
        case "skipped": return AppColors.warning
        case "started": return AppColors.secondary
        default: return AppColors.primary
        }
    }

    private func openOrGenerateWorkout() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            if let workoutID = generatedWorkoutID {
                workout = try await workoutRepository.getWorkoutDetail(workoutId: workoutID)
            } else {
                errorMessage = "No planned workout available for today."
            }
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription
                ?? "Unable to prepare today’s workout."
        }
    }
}

extension ISO8601DateFormatter {
    static let smartFitDate: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .iso8601)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = .current
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()
}
