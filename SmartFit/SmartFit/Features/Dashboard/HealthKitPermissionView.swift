import SwiftUI

struct HealthKitPermissionView: View {
    let permissionState: HealthPermissionState
    let isSyncing: Bool
    let onConnect: () -> Void
    let onManualCheckIn: () -> Void

    var body: some View {
        AppCard(cornerRadius: 24, padding: 24) {
            VStack(alignment: .leading, spacing: 18) {
                Image(systemName: "heart.text.square.fill")
                    .font(.system(size: 30, weight: .semibold))
                    .foregroundStyle(AppColors.primary)
                Text("Readiness needs a signal")
                    .font(AppTypography.title)
                Text(description)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                    dataPill("Sleep")
                    dataPill("HRV")
                    dataPill("Resting HR")
                    dataPill("Steps")
                }
                PrimaryButton(title: "Connect Apple Health", isLoading: isSyncing, systemImage: "heart.fill", action: onConnect)
                SecondaryButton(title: "Manual Check-in", systemImage: "slider.horizontal.3", action: onManualCheckIn)
            }
        }
    }

    private func dataPill(_ title: String) -> some View {
        Text(title)
            .font(AppTypography.caption.weight(.semibold))
            .foregroundStyle(AppColors.textPrimary)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 10)
            .background(AppColors.surfaceElevated)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var description: String {
        switch permissionState {
        case .unavailable:
            return "Apple Health is not available on this device. You can still estimate readiness with a manual check-in."
        case .notDetermined:
            return "SmartFit reads a small set of Apple Health recovery signals to estimate readiness. You can also skip and use manual check-in."
        case .denied:
            return "Apple Health access is currently denied. You can enable it later in Settings, or continue with a manual check-in."
        case .authorized:
            return "Apple Health is connected. Refresh to sync today’s recovery signals."
        }
    }
}
