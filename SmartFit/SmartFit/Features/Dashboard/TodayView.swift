import SwiftUI

struct TodayView: View {
    @EnvironmentObject private var appState: AppState
    @StateObject private var viewModel = TodayViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.readiness == nil {
                    LoadingView(message: "Loading today’s readiness...")
                } else if let readiness = viewModel.readiness {
                    ScrollView {
                        VStack(spacing: 20) {
                            DailyReadinessCard(
                                readiness: readiness,
                                lastSyncDate: viewModel.lastSyncDate,
                                onGenerateWorkout: { viewModel.navigateToWorkoutBuilder = true },
                                onRefresh: { Task { await viewModel.syncHealthAndCalculateReadiness() } }
                            )
                            ReadinessFactorListView(readiness: readiness)
                        }
                        .padding(24)
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
                } else if viewModel.showManualCheckIn || viewModel.healthPermissionState == .denied || viewModel.healthPermissionState == .unavailable {
                    ScrollView {
                        VStack(spacing: 20) {
                            HealthKitPermissionView(
                                permissionState: viewModel.healthPermissionState,
                                isSyncing: viewModel.isSyncingHealth,
                                onConnect: { Task { await viewModel.connectHealthKit() } },
                                onManualCheckIn: { viewModel.showManualCheckIn = true }
                            )
                            if viewModel.showManualCheckIn {
                                ManualCheckInView(
                                    isSubmitting: viewModel.isSyncingHealth,
                                    onSubmit: { submission in
                                        Task { await viewModel.submitManualCheckIn(submission) }
                                    }
                                )
                            }
                        }
                        .padding(24)
                    }
                } else {
                    HealthKitPermissionView(
                        permissionState: viewModel.healthPermissionState,
                        isSyncing: viewModel.isSyncingHealth,
                        onConnect: { Task { await viewModel.connectHealthKit() } },
                        onManualCheckIn: { viewModel.showManualCheckIn = true }
                    )
                    .padding(24)
                }
            }
            .background(AppColors.background.ignoresSafeArea())
            .navigationTitle("Today")
            .navigationDestination(isPresented: $viewModel.navigateToWorkoutBuilder) {
                GenerateWorkoutView(
                    workoutDate: viewModel.workoutDate,
                    readiness: viewModel.readiness,
                    initialEquipment: appState.currentUser?.equipmentTypes ?? [],
                    workoutRepository: appState.environment.workoutRepository,
                    workoutMetricsReader: appState.environment.healthKitWorkoutMetricsReader
                )
            }
            .task {
                viewModel.configure(appState: appState)
                await viewModel.onAppear()
            }
            .overlay(alignment: .bottom) {
                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textPrimary)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .background(AppColors.error)
                        .clipShape(Capsule())
                        .padding(.bottom, 16)
                }
            }
        }
    }
}
