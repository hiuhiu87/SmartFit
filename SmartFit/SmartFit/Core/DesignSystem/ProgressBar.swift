import SwiftUI

struct ProgressBar: View {
    var value: Double
    var tint: Color = AppColors.primary
    var track: Color = AppColors.surfaceMuted
    var height: CGFloat = AppSpacing.sm

    private var normalizedValue: Double {
        min(max(value, 0), 1)
    }

    var body: some View {
        GeometryReader { proxy in
            ZStack(alignment: .leading) {
                Capsule()
                    .fill(track)
                Capsule()
                    .fill(tint)
                    .frame(width: proxy.size.width * normalizedValue)
            }
        }
        .frame(height: height)
        .animation(AppAnimation.standard, value: normalizedValue)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Progress")
        .accessibilityValue("\(Int(normalizedValue * 100)) percent")
    }
}

struct ProgressBar_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()
            VStack(spacing: AppSpacing.lg) {
                ProgressBar(value: 0.72)
                ProgressBar(value: 0.42, tint: AppColors.warning)
            }
            .padding(AppSpacing.xxl)
        }
        .preferredColorScheme(.dark)
        .previewDisplayName("ProgressBar")
    }
}
