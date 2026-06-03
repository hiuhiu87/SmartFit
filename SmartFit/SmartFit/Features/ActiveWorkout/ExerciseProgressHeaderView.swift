import SwiftUI

struct ExerciseProgressHeaderView: View {
    let title: String
    let currentIndex: Int
    let totalCount: Int

    var body: some View {
        AppCard(cornerRadius: 22, padding: 18) {
            VStack(alignment: .leading, spacing: 12) {
                Text(title)
                    .font(AppTypography.title)
                    .foregroundStyle(AppColors.textPrimary)
                    .lineLimit(1)

                HStack {
                    Text("Exercise \(currentIndex) of \(totalCount)")
                        .font(AppTypography.body.weight(.semibold))
                    Spacer()
                    Text(progressPercent)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }

                GeometryReader { proxy in
                    ZStack(alignment: .leading) {
                        Capsule()
                            .fill(AppColors.surfaceMuted)
                            .frame(height: 10)
                        Capsule()
                            .fill(AppColors.primary)
                            .frame(width: max(proxy.size.width * progressValue, 10), height: 10)
                    }
                }
                .frame(height: 10)
            }
        }
    }

    private var progressValue: CGFloat {
        guard totalCount > 0 else { return 0 }
        return CGFloat(currentIndex) / CGFloat(totalCount)
    }

    private var progressPercent: String {
        "\(Int(progressValue * 100))%"
    }
}

#if DEBUG
struct ExerciseProgressHeaderView_Previews: PreviewProvider {
    static var previews: some View {
        ExerciseProgressHeaderView(title: "Chest Dumbbell Day", currentIndex: 2, totalCount: 4)
            .padding()
            .background(AppColors.background)
            .preferredColorScheme(.dark)
    }
}
#endif
