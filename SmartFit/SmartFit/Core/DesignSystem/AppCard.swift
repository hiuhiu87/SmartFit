import SwiftUI

struct AppCard<Content: View>: View {
    var cornerRadius: CGFloat = AppRadius.card
    var padding: CGFloat = AppSpacing.xl
    var background: Color = AppColors.surface
    var borderColor: Color = AppColors.border
    var shadow: AppShadowStyle = AppShadow.card
    var fillsWidth = true
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            content
        }
        .padding(padding)
        .frame(maxWidth: fillsWidth ? .infinity : nil, alignment: .leading)
        .background(background)
        .overlay(
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .stroke(borderColor, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
        .appShadow(shadow)
    }
}

struct ElevatedCard<Content: View>: View {
    var padding: CGFloat = AppSpacing.xxl
    @ViewBuilder let content: Content

    var body: some View {
        AppCard(
            cornerRadius: AppRadius.elevatedCard,
            padding: padding,
            background: AppColors.surfaceElevated,
            shadow: AppShadow.elevated,
            fillsWidth: true,
            content: { content }
        )
    }
}

struct HeroCard<Content: View>: View {
    var padding: CGFloat = AppSpacing.xxl
    @ViewBuilder let content: Content

    var body: some View {
        AppCard(
            cornerRadius: AppRadius.hero,
            padding: padding,
            background: AppColors.surfaceElevated,
            borderColor: AppColors.primary.opacity(0.20),
            shadow: AppShadow.hero,
            fillsWidth: true,
            content: { content }
        )
    }
}

struct AppCard_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()
            VStack(spacing: AppSpacing.lg) {
                AppCard {
                    Text("Base card")
                        .font(AppTypography.title)
                        .foregroundStyle(AppColors.textPrimary)
                }
                ElevatedCard {
                    Text("Elevated card")
                        .font(AppTypography.title)
                        .foregroundStyle(AppColors.textPrimary)
                }
                HeroCard {
                    Text("Hero card")
                        .font(AppTypography.hero)
                        .foregroundStyle(AppColors.textPrimary)
                }
            }
            .padding(AppSpacing.xxl)
        }
        .preferredColorScheme(.dark)
        .previewDisplayName("AppCard")
    }
}
