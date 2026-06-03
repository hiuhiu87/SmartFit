import SwiftUI

struct MuscleDistributionView: View {
    let items: [MuscleDistributionItem]

    var body: some View {
        AppCard(cornerRadius: 24, padding: 20) {
            VStack(alignment: .leading, spacing: 16) {
                SectionHeader(title: "Muscle Distribution", subtitle: "Training balance by completed work")

                if items.isEmpty {
                    Text("No distribution data yet.")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textSecondary)
                } else {
                    ForEach(items) { item in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(item.muscle.replacingOccurrences(of: "_", with: " ").capitalized)
                                    .font(AppTypography.body.weight(.semibold))
                                Spacer()
                                Text("\(item.percentage)%")
                                    .font(AppTypography.caption)
                                    .foregroundStyle(AppColors.textSecondary)
                            }

                            GeometryReader { geometry in
                                ZStack(alignment: .leading) {
                                    Capsule()
                                        .fill(AppColors.surfaceElevated)
                                    Capsule()
                                        .fill(AppColors.primary)
                                        .frame(width: geometry.size.width * CGFloat(item.percentage) / 100)
                                }
                            }
                            .frame(height: 12)

                            Text("\(item.workoutCount) workouts • \(item.setCount) sets • \(Int(item.volume)) kg")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                    }
                }
            }
        }
    }
}

#if DEBUG
struct MuscleDistributionView_Previews: PreviewProvider {
    static var previews: some View {
        MuscleDistributionView(items: ProgressOverviewResponse.mock.muscleDistribution)
            .padding()
            .background(AppColors.background)
            .preferredColorScheme(.dark)
    }
}
#endif
