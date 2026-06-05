import SwiftUI

struct CreateProgramView: View {
    @Environment(\.dismiss) private var dismiss

    let repository: ProgramRepository
    let equipment: [String]
    let onCreated: (TrainingProgramResponse) -> Void

    @State private var goal = "muscle_gain"
    @State private var trainingStyle = "balanced"
    @State private var durationWeeks = 6
    @State private var daysPerWeek = 4
    @State private var sessionDurationMinutes = 60
    @State private var preferredSplit = "upper_lower"
    @State private var focusAreas: Set<String> = []
    @State private var isCreating = false
    @State private var errorMessage: String?

    private let goals = ["muscle_gain", "strength", "fat_loss", "endurance", "general_health"]
    private let trainingStyles = ["balanced", "hypertrophy", "strength", "conditioning", "posture", "glute_core", "returning"]
    private let splits = ["full_body", "upper_lower", "push_pull_legs", "custom"]
    private let availableFocusAreas = ["posture", "back", "chest", "shoulders", "arms", "legs", "core", "conditioning"]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                introCard
                selectionCard(title: "Goal") {
                    optionPicker(values: goals, selection: $goal)
                }
                selectionCard(title: "Training Style") {
                    optionPicker(values: trainingStyles, selection: $trainingStyle)
                }
                scheduleCard
                selectionCard(title: "Preferred Split") {
                    optionPicker(values: splits, selection: $preferredSplit)
                }
                focusAreaCard
                equipmentCard

                if let errorMessage {
                    Text(errorMessage)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.danger)
                }

                PrimaryButton(
                    title: "Create Training Program",
                    isLoading: isCreating,
                    systemImage: "calendar.badge.plus"
                ) {
                    Task { await createProgram() }
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Create Program")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var introCard: some View {
        AppCard {
            VStack(alignment: .leading, spacing: 8) {
                Text("Build the next training block")
                    .font(AppTypography.title)
                Text("SmartFit will create a repeatable weekly plan and adjust each day using your readiness.")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)
            }
        }
    }

    private var scheduleCard: some View {
        AppCard {
            VStack(alignment: .leading, spacing: 18) {
                Text("Schedule")
                    .font(AppTypography.title)
                stepperRow(
                    title: "Duration",
                    value: "\(durationWeeks) weeks",
                    binding: $durationWeeks,
                    range: 2...16,
                    step: 1
                )
                stepperRow(
                    title: "Training days",
                    value: "\(daysPerWeek) days / week",
                    binding: $daysPerWeek,
                    range: 2...5,
                    step: 1
                )
                stepperRow(
                    title: "Session length",
                    value: "\(sessionDurationMinutes) minutes",
                    binding: $sessionDurationMinutes,
                    range: 30...120,
                    step: 15
                )
            }
        }
    }

    private var focusAreaCard: some View {
        selectionCard(title: "Focus Areas") {
            FlowLayout(spacing: 8) {
                ForEach(availableFocusAreas, id: \.self) { area in
                    chip(area, selected: focusAreas.contains(area)) {
                        if focusAreas.contains(area) {
                            focusAreas.remove(area)
                        } else {
                            focusAreas.insert(area)
                        }
                    }
                }
            }
        }
    }

    private var equipmentCard: some View {
        AppCard {
            VStack(alignment: .leading, spacing: 10) {
                Text("Available Equipment")
                    .font(AppTypography.title)
                Text("Uses the equipment already saved in your profile.")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
                FlowLayout(spacing: 8) {
                    ForEach(equipment, id: \.self) { item in
                        chip(item, selected: true, action: {})
                            .allowsHitTesting(false)
                    }
                }
            }
        }
    }

    private func selectionCard<Content: View>(
        title: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        AppCard {
            VStack(alignment: .leading, spacing: 14) {
                Text(title)
                    .font(AppTypography.title)
                content()
            }
        }
    }

    private func optionPicker(values: [String], selection: Binding<String>) -> some View {
        VStack(spacing: 10) {
            ForEach(values, id: \.self) { value in
                SelectableCard(
                    title: value.programDisplayName,
                    subtitle: subtitle(for: value),
                    isSelected: selection.wrappedValue == value
                ) {
                    selection.wrappedValue = value
                }
            }
        }
    }

    private func stepperRow(
        title: String,
        value: String,
        binding: Binding<Int>,
        range: ClosedRange<Int>,
        step: Int
    ) -> some View {
        Stepper(value: binding, in: range, step: step) {
            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
                Text(value)
                    .font(AppTypography.body.weight(.semibold))
            }
        }
    }

    private func chip(_ value: String, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(value.programDisplayName)
                .font(AppTypography.caption.weight(.semibold))
                .foregroundStyle(selected ? AppColors.textInverse : AppColors.textPrimary)
                .padding(.horizontal, 12)
                .padding(.vertical, 9)
                .background(selected ? AppColors.primary : AppColors.surfaceElevated)
                .clipShape(Capsule())
        }
        .buttonStyle(.plain)
    }

    private func subtitle(for value: String) -> String {
        switch value {
        case "muscle_gain": return "Build muscle with progressive weekly volume."
        case "strength": return "Prioritize heavier compound lifting."
        case "fat_loss": return "Combine resistance work with conditioning."
        case "endurance": return "Build work capacity and sustained output."
        case "general_health": return "Balanced strength, movement, and conditioning."
        
        case "balanced": return "Strength, muscle, cardio, and core"
        case "hypertrophy": return "More volume and muscle-focused training"
        case "conditioning": return "More cardio and full-body work"
        case "posture": return "More back, rear delts, and core stability"
        case "glute_core": return "Lower body and core emphasis"
        case "returning": return "Moderate volume and safer exercise choices"
        
        case "full_body": return "Train the whole body each session."
        case "upper_lower": return "Alternate upper and lower focused days."
        case "push_pull_legs": return "Organize sessions by movement function."
        default: return "Use SmartFit’s structured weekly template."
        }
    }

    private func createProgram() async {
        isCreating = true
        errorMessage = nil
        defer { isCreating = false }

        do {
            let program = try await repository.createProgram(
                CreateProgramRequest(
                    goal: goal,
                    durationWeeks: durationWeeks,
                    daysPerWeek: daysPerWeek,
                    sessionDurationMinutes: sessionDurationMinutes,
                    preferredSplit: preferredSplit,
                    focusAreas: Array(focusAreas).sorted(),
                    generationMode: "auto",
                    trainingStyle: trainingStyle
                )
            )
            onCreated(program)
            dismiss()
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to create program."
        }
    }
}

private struct FlowLayout: Layout {
    let spacing: CGFloat

    func sizeThatFits(
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) -> CGSize {
        let result = layout(subviews: subviews, width: proposal.width ?? 0)
        return result.size
    }

    func placeSubviews(
        in bounds: CGRect,
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) {
        let result = layout(subviews: subviews, width: bounds.width)
        for (index, point) in result.points.enumerated() {
            subviews[index].place(
                at: CGPoint(x: bounds.minX + point.x, y: bounds.minY + point.y),
                proposal: .unspecified
            )
        }
    }

    private func layout(subviews: Subviews, width: CGFloat) -> (size: CGSize, points: [CGPoint]) {
        var points: [CGPoint] = []
        var position = CGPoint.zero
        var rowHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if position.x + size.width > width, position.x > 0 {
                position.x = 0
                position.y += rowHeight + spacing
                rowHeight = 0
            }
            points.append(position)
            position.x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        return (CGSize(width: width, height: position.y + rowHeight), points)
    }
}
