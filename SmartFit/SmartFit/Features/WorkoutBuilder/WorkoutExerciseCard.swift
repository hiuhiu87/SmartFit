import SwiftUI

struct WorkoutExerciseCard: View {
    let exercise: WorkoutExerciseResponse

    var body: some View {
        AppCard(cornerRadius: 20, padding: 18) {
            VStack(alignment: .leading, spacing: 14) {
                HStack(alignment: .top, spacing: 12) {
                    Text("\(exercise.orderIndex)")
                        .font(AppTypography.headline)
                        .foregroundStyle(AppColors.textInverse)
                        .frame(width: 34, height: 34)
                        .background(AppColors.primary)
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                    VStack(alignment: .leading, spacing: 6) {
                        Text(exercise.name)
                            .font(AppTypography.headline)
                        HStack(spacing: 8) {
                            StatusBadge(title: exercise.primaryMuscle.capitalized, color: AppColors.primary)
                            StatusBadge(title: exercise.equipment.replacingOccurrences(of: "_", with: " ").capitalized, color: AppColors.secondary)
                        }
                    }
                    Spacer()
                }

                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 8) {
                    stat("Sets", "\(exercise.targetSets)")
                    stat("Reps", exercise.targetReps)
                    if let restSeconds = exercise.restSeconds {
                        stat("Rest", "\(restSeconds)s")
                    }
                    if let targetRpe = exercise.targetRpe {
                        stat("RPE", "\(targetRpe)")
                    }
                }

                if let notes = exercise.notes, !notes.isEmpty {
                    Text(notes)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }
            }
        }
    }

    private func stat(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
            Text(value)
                .font(AppTypography.body.weight(.semibold))
                .lineLimit(1)
                .minimumScaleFactor(0.75)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(AppColors.surfaceElevated)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

#if DEBUG
struct WorkoutExerciseCard_Previews: PreviewProvider {
    static var previews: some View {
        WorkoutExerciseCard(exercise: WorkoutPlanResponse.mockAI.exercises[0])
            .padding()
            .background(AppColors.background)
            .preferredColorScheme(.dark)
    }
}
#endif
