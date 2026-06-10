import SwiftUI

struct ProgramPhaseBadge: View {
    let phase: String

    var body: some View {
        Text(phase.programDisplayName)
            .font(AppTypography.caption.weight(.semibold))
            .foregroundStyle(phaseColor)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(phaseColor.opacity(0.12))
            .clipShape(Capsule())
    }

    private var phaseColor: Color {
        switch phase.lowercased() {
        case "foundation": return AppColors.primary
        case "accumulation": return AppColors.success
        case "intensification": return AppColors.warning
        case "deload": return AppColors.secondary
        case "consolidation": return AppColors.textPrimary
        default: return AppColors.textSecondary
        }
    }
}
