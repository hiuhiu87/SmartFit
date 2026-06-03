import SwiftUI

struct StatusBadge: View {
    let title: String
    var color: Color = AppColors.primary

    var body: some View {
        Text(title)
            .font(AppTypography.caption.weight(.semibold))
            .foregroundStyle(color)
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .background(color.opacity(0.14))
            .overlay(
                Capsule()
                    .stroke(color.opacity(0.35), lineWidth: 1)
            )
            .clipShape(Capsule())
    }
}
