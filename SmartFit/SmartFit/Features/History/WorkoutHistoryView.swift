import SwiftUI

struct WorkoutHistoryView: View {
    @StateObject private var viewModel: WorkoutHistoryViewModel
    private let repository: HistoryRepositoryProtocol

    init(repository: HistoryRepositoryProtocol) {
        self.repository = repository
        _viewModel = StateObject(wrappedValue: WorkoutHistoryViewModel(repository: repository))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                filterSection

                if viewModel.isLoading && viewModel.items.isEmpty {
                    LoadingStateView(message: "Loading workout history...")
                } else if let errorMessage = viewModel.errorMessage, viewModel.items.isEmpty {
                    ErrorStateView(message: errorMessage) {
                        Task { await viewModel.loadInitial() }
                    }
                    .frame(height: 280)
                } else if viewModel.items.isEmpty {
                    emptyState
                } else {
                    LazyVStack(spacing: 14) {
                        ForEach(viewModel.items) { item in
                            NavigationLink {
                                WorkoutDetailView(
                                    workoutId: item.workoutId,
                                    repository: repository,
                                    historyItem: item
                                )
                            } label: {
                                WorkoutHistoryRowView(item: item)
                            }
                            .buttonStyle(.plain)
                            .task {
                                await viewModel.loadMoreIfNeeded(currentItem: item)
                            }
                        }

                        if viewModel.isLoadingMore {
                            ProgressView()
                                .tint(AppColors.primary)
                                .padding(.vertical, 16)
                        }
                    }
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("History")
        .navigationBarTitleDisplayMode(.large)
        .refreshable {
            await viewModel.refresh()
        }
        .task {
            await viewModel.loadInitial()
        }
    }

    private var filterSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Filters")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    filterChip(title: "All", value: nil)
                    filterChip(title: "Completed", value: "completed")
                    filterChip(title: "Started", value: "started")
                    filterChip(title: "Generated", value: "generated")
                }
            }
        }
    }

    private func filterChip(title: String, value: String?) -> some View {
        let isSelected = viewModel.selectedStatusFilter == value
        return Button {
            Task { await viewModel.applyStatusFilter(value) }
        } label: {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(isSelected ? AppColors.textInverse : AppColors.textPrimary)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(isSelected ? AppColors.primary : AppColors.surfaceElevated)
                .clipShape(Capsule())
        }
        .buttonStyle(.plain)
    }

    private var emptyState: some View {
        EmptyStateView(
            title: "No workouts yet",
            message: "Complete your first workout to see duration, volume, and training notes here.",
            systemImage: "figure.strengthtraining.traditional"
        )
    }
}

#if DEBUG
struct WorkoutHistoryView_Previews: PreviewProvider {
    private final class PreviewHistoryRepository: HistoryRepositoryProtocol {
        func getWorkoutHistory(limit: Int, offset: Int, status: String?, fromDate: String?, toDate: String?) async throws -> WorkoutHistoryResponse {
            .init(items: [.mockCompleted, .mockStarted], limit: 20, offset: 0, total: 2)
        }

        func getWorkoutDetail(workoutId: String) async throws -> WorkoutPlanResponse {
            .mockAI
        }
    }

    static var previews: some View {
        NavigationStack {
            WorkoutHistoryView(repository: PreviewHistoryRepository())
        }
        .preferredColorScheme(.dark)
    }
}
#endif
