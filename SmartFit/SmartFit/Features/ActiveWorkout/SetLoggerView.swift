import SwiftUI

struct SetLoggerView: View {
    @Binding var weight: Double?
    @Binding var reps: Int
    @Binding var rpe: Int?

    let setNumber: Int
    let targetSets: Int
    let targetReps: String
    let targetRpe: Int?
    let isLoading: Bool
    let onComplete: () -> Void

    var body: some View {
        AppCard(cornerRadius: 24, padding: 20) {
            VStack(alignment: .leading, spacing: 18) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Log Set \(setNumber) of \(targetSets)")
                        .font(AppTypography.title)
                    Text("Target: \(targetReps)" + (targetRpe.map { " • RPE \($0)" } ?? ""))
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }

                metricRow(
                    title: "Weight",
                    value: weight.map { String(format: "%.1f kg", $0) } ?? "Bodyweight",
                    decrement: { adjustWeight(by: -2.5) },
                    increment: { adjustWeight(by: 2.5) }
                )

                metricRow(
                    title: "Reps",
                    value: "\(reps)",
                    decrement: { reps = max(0, reps - 1) },
                    increment: { reps += 1 }
                )

                VStack(alignment: .leading, spacing: 10) {
                    Text("RPE")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)

                    LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: 5), spacing: 8) {
                        ForEach(1...10, id: \.self) { value in
                            Button {
                                rpe = value
                            } label: {
                                Text("\(value)")
                                    .font(AppTypography.body.weight(.semibold))
                                    .foregroundStyle(rpe == value ? AppColors.textInverse : AppColors.textPrimary)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 12)
                                    .background(rpe == value ? AppColors.primary : AppColors.surfaceElevated)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                                            .stroke(rpe == value ? AppColors.primary : AppColors.border, lineWidth: 1)
                                    )
                                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }

                PrimaryButton(title: "Complete Set", isLoading: isLoading, action: onComplete)
            }
        }
    }

    private func metricRow(
        title: String,
        value: String,
        decrement: @escaping () -> Void,
        increment: @escaping () -> Void
    ) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)

            HStack(spacing: 12) {
                StepButton(symbol: "minus", action: decrement)
                Text(value)
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                    .foregroundStyle(AppColors.textPrimary)
                    .frame(maxWidth: .infinity)
                StepButton(symbol: "plus", action: increment)
            }
        }
    }

    private func adjustWeight(by amount: Double) {
        let next = (weight ?? 0) + amount
        if next <= 0 {
            weight = nil
        } else {
            weight = max(0, next)
        }
    }
}

private struct StepButton: View {
    let symbol: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: symbol)
                .font(.system(size: 18, weight: .bold))
                .foregroundStyle(AppColors.textPrimary)
                .frame(width: 48, height: 48)
                .background(AppColors.surfaceElevated)
                .overlay(
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .stroke(AppColors.border, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}

#if DEBUG
struct SetLoggerView_Previews: PreviewProvider {
    struct PreviewContainer: View {
        @State private var weight: Double? = 20
        @State private var reps = 10
        @State private var rpe: Int? = 7

        var body: some View {
            SetLoggerView(
                weight: $weight,
                reps: $reps,
                rpe: $rpe,
                setNumber: 2,
                targetSets: 4,
                targetReps: "8-10",
                targetRpe: 7,
                isLoading: false,
                onComplete: {}
            )
        }
    }

    static var previews: some View {
        PreviewContainer()
            .padding()
            .background(AppColors.background)
            .preferredColorScheme(.dark)
    }
}
#endif
