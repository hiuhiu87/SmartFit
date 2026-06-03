import SwiftUI

struct ManualCheckInView: View {
    let isSubmitting: Bool
    let onSubmit: (ManualCheckInSubmission) -> Void

    @State private var sleepHours = 7.0
    @State private var energyLevel = 6.0
    @State private var stressLevel = 4.0
    @State private var sorenessLevel = 4.0
    @State private var painNote = ""

    var body: some View {
        AppCard(cornerRadius: 24, padding: 24) {
            VStack(alignment: .leading, spacing: 18) {
                Text("Manual Check-in")
                    .font(AppTypography.title)

                sliderRow(title: "Sleep Hours", value: $sleepHours, range: 0...12, step: 0.5)
                sliderRow(title: "Energy Level", value: $energyLevel, range: 1...10, step: 1)
                sliderRow(title: "Stress Level", value: $stressLevel, range: 1...10, step: 1)
                sliderRow(title: "Soreness Level", value: $sorenessLevel, range: 1...10, step: 1)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Pain Note")
                        .font(AppTypography.body.weight(.semibold))
                    AppInputField(cornerRadius: 16) {
                        TextField("Optional note about pain or discomfort", text: $painNote, axis: .vertical)
                            .lineLimit(3, reservesSpace: true)
                    }
                }

                PrimaryButton(title: "Calculate Readiness", isLoading: isSubmitting) {
                    onSubmit(
                        ManualCheckInSubmission(
                            date: HealthSummaryBuilder().dateString(for: Date()),
                            sleepHours: sleepHours,
                            energyLevel: Int(energyLevel),
                            stressLevel: Int(stressLevel),
                            sorenessLevel: Int(sorenessLevel),
                            painNote: painNote.isEmpty ? nil : painNote
                        )
                    )
                }
            }
        }
    }

    private func sliderRow(
        title: String,
        value: Binding<Double>,
        range: ClosedRange<Double>,
        step: Double
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(title)
                    .font(AppTypography.body.weight(.semibold))
                Spacer()
                Text(step == 1 ? "\(Int(value.wrappedValue))" : String(format: "%.1f", value.wrappedValue))
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
            }
            Slider(value: value, in: range, step: step)
                .tint(AppColors.primary)
        }
    }
}
