import SwiftUI

struct ProgramDetailView: View {
    let program: TrainingProgramResponse
    let todayWorkout: ProgramTodayWorkoutResponse?
    let readiness: ReadinessResponse?
    let equipment: [String]
    let programRepository: ProgramRepository
    let workoutRepository: WorkoutRepository
    let workoutMetricsReader: HealthKitWorkoutMetricsReader?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                summaryCard

                if let todayWorkout, todayWorkout.scheduled {
                    NavigationLink {
                        ProgramTodayWorkoutView(
                            program: program,
                            todayWorkout: todayWorkout,
                            readiness: readiness,
                            equipment: equipment,
                            programRepository: programRepository,
                            workoutRepository: workoutRepository,
                            workoutMetricsReader: workoutMetricsReader
                        )
                    } label: {
                        todayCard(todayWorkout)
                    }
                    .buttonStyle(.plain)
                }

                WeeklyStructureView(
                    templates: program.weeklyStructure,
                    currentDayIndex: todayWorkout?.scheduled == true
                        ? todayWorkout?.dayIndex
                        : nil
                )

                if !program.focusAreas.isEmpty {
                    AppCard {
                        VStack(alignment: .leading, spacing: 10) {
                            Text("Program Focus")
                                .font(AppTypography.title)
                            Text(program.focusAreas.map(\.programDisplayName).joined(separator: " · "))
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                    }
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Training Program")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var summaryCard: some View {
        AppCard(cornerRadius: 24, padding: 22) {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    VStack(alignment: .leading, spacing: 5) {
                        Text(program.name)
                            .font(AppTypography.hero)
                        Text(
                            "\(program.goal.programDisplayName) · "
                                + "\(program.trainingLevel.programDisplayName)"
                        )
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                    }
                    Spacer()
                    StatusBadge(title: program.status.programDisplayName)
                }

                ProgressView(value: program.progress)
                    .tint(AppColors.primary)

                HStack {
                    metric("Week", "\(program.currentWeek)/\(program.durationWeeks)")
                    metric("Frequency", "\(program.daysPerWeek)x")
                    metric("Session", "\(program.sessionDurationMinutes)m")
                }
            }
        }
    }

    private func todayCard(_ workout: ProgramTodayWorkoutResponse) -> some View {
        AppCard(background: AppColors.primary.opacity(0.12)) {
            HStack(spacing: 14) {
                Image(systemName: "figure.strengthtraining.traditional")
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundStyle(AppColors.primary)
                VStack(alignment: .leading, spacing: 4) {
                    Text("Today’s Workout")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                    Text(workout.template?.title ?? "Scheduled Session")
                        .font(AppTypography.body.weight(.semibold))
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .foregroundStyle(AppColors.textSecondary)
            }
        }
    }

    private func metric(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
            Text(value)
                .font(AppTypography.body.weight(.semibold))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
