import SwiftUI

struct WorkoutSummaryView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var navigateToHistory = false

    let workout: WorkoutPlanResponse
    let completion: CompleteWorkoutResponse
    let difficultyFeedback: String?
    let energyAfter: Int?
    let durationMinutes: Int?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                AppCard(cornerRadius: 24, padding: 22) {
                    VStack(alignment: .leading, spacing: 16) {
                        Text("Workout Saved")
                            .font(AppTypography.hero)
                        Text(workout.title)
                            .font(AppTypography.title)
                            .foregroundStyle(AppColors.textSecondary)

                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                            MetricCard(title: "Volume", value: String(format: "%.0f", completion.totalVolume), subtitle: "kg total")
                            MetricCard(title: "Exercises", value: "\(workout.exercises.count)", subtitle: "completed")
                            if let durationMinutes {
                                MetricCard(title: "Duration", value: "\(durationMinutes)", subtitle: "minutes")
                            }
                            if let energyAfter {
                                MetricCard(title: "Energy", value: "\(energyAfter)", subtitle: "after workout")
                            }
                        }
                        if let difficultyFeedback {
                            detailLine("Difficulty", difficultyFeedback.replacingOccurrences(of: "_", with: " ").capitalized)
                        }
                    }
                }

                VStack(spacing: 12) {
                    PrimaryButton(title: "Back to Today", systemImage: "house.fill") {
                        dismiss()
                    }
                    SecondaryButton(title: "View History", systemImage: "clock.arrow.circlepath") {
                        navigateToHistory = true
                    }
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Workout Summary")
        .navigationBarTitleDisplayMode(.inline)
        .navigationDestination(isPresented: $navigateToHistory) {
            HistoryView()
        }
    }

    private func detailLine(_ title: String, _ value: String) -> some View {
        HStack(alignment: .top) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
                .frame(width: 120, alignment: .leading)
            Text(value)
                .font(AppTypography.body.weight(.semibold))
        }
    }
}

#if DEBUG
struct WorkoutSummaryView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack {
            WorkoutSummaryView(
                workout: .mockAI,
                completion: CompleteWorkoutResponse(
                    workoutId: WorkoutPlanResponse.mockAI.workoutID,
                    workoutLogId: UUID().uuidString,
                    status: "completed",
                    totalVolume: 4250,
                    completedAt: "2026-06-02T12:00:00Z"
                ),
                difficultyFeedback: "just_right",
                energyAfter: 8,
                durationMinutes: 54
            )
        }
        .preferredColorScheme(.dark)
    }
}
#endif
