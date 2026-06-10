import SwiftUI

struct CreateProgramView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel: CreateProgramViewModel

    init(
        repository: ProgramRepositoryProtocol,
        equipment: [String],
        onCreated: @escaping (CreateProgramResponse) -> Void
    ) {
        _viewModel = StateObject(
            wrappedValue: CreateProgramViewModel(
                repository: repository,
                equipment: equipment,
                onCreated: onCreated
            )
        )
    }

    private let goals = ["muscle_gain", "strength", "fat_loss", "endurance", "general_health"]
    private let trainingStyles = ["balanced", "hypertrophy", "strength", "conditioning", "posture", "glute_core", "returning"]
    private let splits = ["full_body", "upper_lower", "push_pull_legs", "custom"]
    private let availableFocusAreas = ["posture", "back", "chest", "shoulders", "arms", "legs", "core", "conditioning"]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                introCard
                selectionCard(title: "Goal") {
                    optionPicker(values: goals, selection: $viewModel.goal)
                }
                selectionCard(title: "Training Style") {
                    optionPicker(values: trainingStyles, selection: $viewModel.trainingStyle)
                }
                scheduleCard
                selectionCard(title: "Preferred Split") {
                    optionPicker(values: splits, selection: $viewModel.preferredSplit)
                }
                focusAreaCard
                equipmentCard

                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.danger)
                }

                PrimaryButton(
                    title: "Create Training Program",
                    isLoading: viewModel.isCreating,
                    systemImage: "calendar.badge.plus"
                ) {
                    Task {
                        let success = await viewModel.createProgram()
                        if success {
                            dismiss()
                        }
                    }
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
                    value: "\(viewModel.durationWeeks) weeks",
                    binding: $viewModel.durationWeeks,
                    range: 2...16,
                    step: 1
                )
                stepperRow(
                    title: "Training days",
                    value: "\(viewModel.daysPerWeek) days / week",
                    binding: $viewModel.daysPerWeek,
                    range: 2...6,
                    step: 1
                )
                stepperRow(
                    title: "Session length",
                    value: "\(viewModel.sessionDurationMinutes) minutes",
                    binding: $viewModel.sessionDurationMinutes,
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
                    chip(area, selected: viewModel.focusAreas.contains(area)) {
                        if viewModel.focusAreas.contains(area) {
                            viewModel.focusAreas.remove(area)
                        } else {
                            viewModel.focusAreas.insert(area)
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
                    ForEach(viewModel.equipment, id: \.self) { item in
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
}

private struct FlowLayout: Layout {
    let spacing: CGFloat

    func sizeThatFits(
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) -> CGSize {
        let sizes = subviews.map { $0.sizeThatFits(.unspecified) }
        var width: CGFloat = 0
        var height: CGFloat = 0
        var currentX: CGFloat = 0
        var currentY: CGFloat = 0
        var maxHeight: CGFloat = 0

        let maxW = proposal.width ?? .infinity

        for size in sizes {
            if currentX + size.width > maxW {
                currentX = 0
                currentY += maxHeight + spacing
                maxHeight = 0
            }
            currentX += size.width + spacing
            maxHeight = max(maxHeight, size.height)
            width = max(width, currentX)
            height = max(height, currentY + maxHeight)
        }
        return CGSize(width: width, height: height)
    }

    func placeSubviews(
        in bounds: CGRect,
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) {
        let sizes = subviews.map { $0.sizeThatFits(.unspecified) }
        var currentX: CGFloat = bounds.minX
        var currentY: CGFloat = bounds.minY
        var maxHeight: CGFloat = 0

        for (index, subview) in subviews.enumerated() {
            let size = sizes[index]
            if currentX + size.width > bounds.maxX {
                currentX = bounds.minX
                currentY += maxHeight + spacing
                maxHeight = 0
            }
            subview.place(
                at: CGPoint(x: currentX, y: currentY),
                proposal: ProposedViewSize(size)
            )
            currentX += size.width + spacing
            maxHeight = max(maxHeight, size.height)
        }
    }
}
