import SwiftUI

enum ReadinessStyle {
    static func color(for category: String) -> Color {
        switch category {
        case "excellent":
            return AppColors.success
        case "good":
            return AppColors.primary
        case "moderate":
            return AppColors.warning
        case "low":
            return AppColors.warning.opacity(0.85)
        case "very_low":
            return AppColors.error
        default:
            return AppColors.primary
        }
    }
}
