import SwiftUI

struct PrimaryButton: View {
    let title: String
    var isLoading = false
    var systemImage: String?
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                if isLoading {
                    ProgressView()
                        .tint(AppColors.textInverse)
                } else if let systemImage {
                    Image(systemName: systemImage)
                        .font(.system(size: 15, weight: .bold))
                }
                Text(title)
                    .font(AppTypography.body.weight(.semibold))
            }
            .foregroundStyle(AppColors.textInverse)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 15)
            .background(AppColors.primary)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .disabled(isLoading)
        .opacity(isLoading ? 0.75 : 1)
    }
}
