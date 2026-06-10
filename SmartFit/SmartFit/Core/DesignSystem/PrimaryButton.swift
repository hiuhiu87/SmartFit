import SwiftUI

struct PrimaryButton: View {
    let title: String
    var isLoading = false
    var systemImage: String?
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: AppSpacing.sm) {
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
            .padding(.vertical, AppSpacing.lg)
            .background(AppColors.primary)
            .clipShape(RoundedRectangle(cornerRadius: AppRadius.button, style: .continuous))
        }
        .buttonStyle(.plain)
        .disabled(isLoading)
        .opacity(isLoading ? 0.75 : 1)
        .animation(AppAnimation.quick, value: isLoading)
    }
}

struct PrimaryButton_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()
            VStack(spacing: AppSpacing.md) {
                PrimaryButton(title: "Start Workout", systemImage: "play.fill") {}
                PrimaryButton(title: "Loading", isLoading: true) {}
            }
            .padding(AppSpacing.xxl)
        }
        .preferredColorScheme(.dark)
        .previewDisplayName("PrimaryButton")
    }
}
