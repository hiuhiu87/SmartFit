import SwiftUI

struct ProgressOverviewView: View {
    @StateObject private var viewModel: ProgressOverviewViewModel

    init(repository: ProgressRepositoryProtocol) {
        _viewModel = StateObject(wrappedValue: ProgressOverviewViewModel(repository: repository))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                if viewModel.isLoading && viewModel.overview == nil && viewModel.personalRecords.isEmpty && viewModel.weeklyReport == nil {
                    LoadingStateView(message: "Loading progress insights...")
                } else if let errorMessage = viewModel.errorMessage, viewModel.overview == nil && viewModel.personalRecords.isEmpty && viewModel.weeklyReport == nil {
                    ErrorStateView(message: errorMessage) {
                        Task { await viewModel.refresh() }
                    }
                    .frame(height: 280)
                } else if isEmpty {
                    emptyState
                } else {
                    if let errorMessage = viewModel.errorMessage {
                        Text(errorMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.textPrimary)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 10)
                            .background(AppColors.warning)
                            .clipShape(Capsule())
                    }

                    if let overview = viewModel.overview {
                        summaryCard(overview)

                        if let latest = overview.latestCompletedWorkout {
                            latestWorkoutCard(latest)
                        }

                        MuscleDistributionView(items: overview.muscleDistribution)
                    }

                    PersonalRecordsView(items: viewModel.personalRecords)
                    WeeklyReportView(report: viewModel.weeklyReport)
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Progress")
        .navigationBarTitleDisplayMode(.large)
        .refreshable {
            await viewModel.refresh()
        }
        .task {
            await viewModel.load()
        }
    }

    private var isEmpty: Bool {
        viewModel.overview == nil && viewModel.personalRecords.isEmpty && viewModel.weeklyReport == nil
    }

    private var emptyState: some View {
        EmptyStateView(
            title: "No progress yet",
            message: "Progress insights will appear after you complete your first workout.",
            systemImage: "chart.line.uptrend.xyaxis"
        )
    }

    private func summaryCard(_ overview: ProgressOverviewResponse) -> some View {
        AppCard(cornerRadius: 24, padding: 22) {
            VStack(alignment: .leading, spacing: 16) {
                SectionHeader(title: "This Week", subtitle: "Training consistency and load")

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                    MetricCard(title: "Completed", value: "\(overview.weeklyWorkoutsCompleted)/\(overview.weeklyWorkoutTarget)")
                    MetricCard(title: "Consistency", value: "\(overview.consistencyPercentage)%", tint: AppColors.success)
                    MetricCard(title: "Volume", value: "\(Int(overview.totalVolumeThisWeek))", subtitle: "kg this week", tint: AppColors.secondary)
                    MetricCard(
                        title: "Avg Readiness",
                        value: overview.averageReadinessThisWeek.map { String(format: "%.0f", $0) } ?? "-"
                    )
                }
            }
        }
    }

    private func latestWorkoutCard(_ latest: LatestCompletedWorkout) -> some View {
        AppCard(cornerRadius: 24, padding: 20) {
            VStack(alignment: .leading, spacing: 10) {
                SectionHeader(title: "Latest Completed Workout")
                Text(latest.title)
                    .font(AppTypography.headline)
                HStack(spacing: 10) {
                    if let focus = latest.focusMuscle {
                        pill(focus.replacingOccurrences(of: "_", with: " ").capitalized)
                    }
                    if let duration = latest.durationMinutes {
                        pill("\(duration) min")
                    }
                    if let volume = latest.totalVolume {
                        pill("\(Int(volume)) kg")
                    }
                }
                if let completedAt = latest.completedAt {
                    Text(WorkoutDateFormatting.displayDateTime(from: completedAt))
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }
            }
        }
    }

    private func pill(_ value: String) -> some View {
        Text(value)
            .font(AppTypography.caption)
            .foregroundStyle(AppColors.textPrimary)
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(AppColors.surfaceElevated)
            .clipShape(Capsule())
    }
}

#if DEBUG
struct ProgressOverviewView_Previews: PreviewProvider {
    private final class PreviewProgressRepository: ProgressRepositoryProtocol {
        func getProgressOverview(fromDate: String?, toDate: String?) async throws -> ProgressOverviewResponse { .mock }
        func getPersonalRecords(limit: Int, exerciseId: String?, metric: String?) async throws -> PersonalRecordsResponse {
            .init(items: [.mock], limit: 10, total: 1)
        }
        func getWeeklyReport(weekStart: String?) async throws -> WeeklyReportResponse { .mock }
    }

    static var previews: some View {
        NavigationStack {
            ProgressOverviewView(repository: PreviewProgressRepository())
        }
        .preferredColorScheme(.dark)
    }
}
#endif
