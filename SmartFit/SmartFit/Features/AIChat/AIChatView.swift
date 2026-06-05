import SwiftUI

struct AIChatView: View {
    @StateObject private var viewModel: AIChatViewModel

    init(
        workout: WorkoutPlanResponse,
        selectedExercise: WorkoutExerciseResponse?,
        repository: AIChatRepository
    ) {
        _viewModel = StateObject(
            wrappedValue: AIChatViewModel(
                workout: workout,
                selectedExercise: selectedExercise,
                repository: repository
            )
        )
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                header

                if viewModel.isLoadingHistory {
                    LoadingView(message: "Loading coach history...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    messagesList
                }

                composer
            }
            .background(AppColors.background.ignoresSafeArea())
            .navigationTitle("AI Coach")
            .navigationBarTitleDisplayMode(.inline)
            .task {
                await viewModel.loadHistory()
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(viewModel.title)
                .font(AppTypography.headline)
                .foregroundStyle(AppColors.textPrimary)
            Text(viewModel.subtitle)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 20)
        .padding(.vertical, 14)
        .background(AppColors.backgroundSecondary)
    }

    private var messagesList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 14) {
                    if viewModel.messages.isEmpty {
                        emptyState
                    } else {
                        ForEach(viewModel.messages) { message in
                            messageBubble(message)
                                .id(message.id)
                        }
                    }

                    if let errorMessage = viewModel.errorMessage {
                        Text(errorMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.error)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.top, 4)
                    }
                }
                .padding(20)
            }
            .onChange(of: viewModel.messages.count) { _, _ in
                guard let lastMessage = viewModel.messages.last else { return }
                withAnimation(.easeOut(duration: 0.2)) {
                    proxy.scrollTo(lastMessage.id, anchor: .bottom)
                }
            }
        }
    }

    private var emptyState: some View {
        AppCard(cornerRadius: 22, padding: 18) {
            VStack(alignment: .leading, spacing: 10) {
                Text("Ask your coach")
                    .font(AppTypography.title)
                    .foregroundStyle(AppColors.textPrimary)
                Text("Examples: “Should I reduce load?”, “How should this feel?”, or “Give me a safer substitute.”")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func messageBubble(_ message: AIChatMessage) -> some View {
        HStack {
            if message.isUser {
                Spacer(minLength: 44)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text(message.message)
                    .font(AppTypography.body)
                    .foregroundStyle(message.isUser ? AppColors.textInverse : AppColors.textPrimary)

                if let action = message.suggestedAction {
                    suggestedActionView(action)
                }
            }
            .padding(14)
            .background(message.isUser ? AppColors.primary : AppColors.surfaceElevated)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))

            if !message.isUser {
                Spacer(minLength: 44)
            }
        }
    }

    private func suggestedActionView(_ action: AIChatSuggestedAction) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(action.type.replacingOccurrences(of: "_", with: " ").capitalized)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.secondary)

            if let exerciseName = action.exerciseName {
                Text(exerciseName)
                    .font(AppTypography.body.weight(.semibold))
            }

            HStack(spacing: 8) {
                if let targetSets = action.targetSets {
                    StatusBadge(title: "\(targetSets) sets")
                }
                if let targetReps = action.targetReps {
                    StatusBadge(title: targetReps)
                }
                if let targetRpe = action.targetRpe {
                    StatusBadge(title: "RPE \(targetRpe)")
                }
            }

            if let reason = action.reason {
                Text(reason)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
            }
        }
        .padding(10)
        .background(AppColors.surface)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var composer: some View {
        VStack(spacing: 10) {
            HStack(alignment: .bottom, spacing: 10) {
                AppInputField(cornerRadius: 18) {
                    TextField("Ask for coaching guidance...", text: $viewModel.draftMessage, axis: .vertical)
                        .lineLimit(1...4)
                        .font(AppTypography.body)
                }

                Button {
                    Task { await viewModel.sendMessage() }
                } label: {
                    Image(systemName: viewModel.isSending ? "hourglass" : "paperplane.fill")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundStyle(AppColors.textInverse)
                        .frame(width: 46, height: 46)
                        .background(AppColors.primary)
                        .clipShape(Circle())
                }
                .disabled(viewModel.isSending || viewModel.draftMessage.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                .opacity(viewModel.isSending ? 0.7 : 1)
            }
        }
        .padding(16)
        .background(AppColors.backgroundSecondary)
    }
}

#if DEBUG
struct AIChatView_Previews: PreviewProvider {
    static var previews: some View {
        AIChatView(
            workout: .mockAI,
            selectedExercise: WorkoutPlanResponse.mockAI.exercises.first,
            repository: AppEnvironment.bootstrap().aiChatRepository
        )
        .preferredColorScheme(.dark)
    }
}
#endif
