import SwiftUI

struct RestTimerView: View {
    let secondsRemaining: Int
    let onSkip: () -> Void
    let onAdd15: () -> Void
    let onMinus15: () -> Void

    var body: some View {
        AppCard(cornerRadius: 24, padding: 24) {
            VStack(spacing: 18) {
                Text("Rest Timer")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)

                Text(timeText)
                    .font(.system(size: 70, weight: .bold, design: .rounded))
                    .foregroundStyle(AppColors.primary)
                    .monospacedDigit()

                HStack(spacing: 12) {
                    SecondaryButton(title: "-15s", action: onMinus15)
                    SecondaryButton(title: "+15s", action: onAdd15)
                }

                PrimaryButton(title: "Start Next Set", systemImage: "play.fill", action: onSkip)
            }
            .frame(maxWidth: .infinity)
        }
    }

    private var timeText: String {
        let minutes = secondsRemaining / 60
        let seconds = secondsRemaining % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }
}

#if DEBUG
struct RestTimerView_Previews: PreviewProvider {
    static var previews: some View {
        RestTimerView(
            secondsRemaining: 75,
            onSkip: {},
            onAdd15: {},
            onMinus15: {}
        )
        .padding()
        .background(AppColors.background)
        .preferredColorScheme(.dark)
    }
}
#endif
