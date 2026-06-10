import Combine
import Foundation

@MainActor
final class WorkoutHistoryViewModel: ObservableObject {
    @Published var items: [WorkoutHistoryItem] = []
    @Published var isLoading = false
    @Published var isLoadingMore = false
    @Published var errorMessage: String?
    @Published var selectedStatusFilter: String?
    @Published var limit = 20
    @Published var offset = 0
    @Published var total = 0

    private let repository: HistoryRepositoryProtocol

    init(repository: HistoryRepositoryProtocol) {
        self.repository = repository
    }

    var hasMore: Bool {
        items.count < total
    }

    func loadInitial() async {
        guard !isLoading else { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let response = try await repository.getWorkoutHistory(
                limit: limit,
                offset: 0,
                status: selectedStatusFilter,
                fromDate: nil,
                toDate: nil
            )
            items = response.items
            offset = response.items.count
            total = response.total
        } catch {
            if error.isCancellation { return }
            errorMessage = Self.message(for: error)
        }
    }

    func refresh() async {
        await loadInitial()
    }

    func loadMoreIfNeeded(currentItem: WorkoutHistoryItem) async {
        guard !isLoadingMore, !isLoading, hasMore else { return }
        guard items.last?.id == currentItem.id || items.suffix(3).contains(where: { $0.id == currentItem.id }) else { return }

        isLoadingMore = true
        defer { isLoadingMore = false }

        do {
            let response = try await repository.getWorkoutHistory(
                limit: limit,
                offset: offset,
                status: selectedStatusFilter,
                fromDate: nil,
                toDate: nil
            )
            items.append(contentsOf: response.items)
            offset += response.items.count
            total = response.total
        } catch {
            if error.isCancellation { return }
            errorMessage = Self.message(for: error)
        }
    }

    func applyStatusFilter(_ status: String?) async {
        guard selectedStatusFilter != status else { return }
        selectedStatusFilter = status
        await loadInitial()
    }

    private static func message(for error: Error) -> String {
        (error as? LocalizedError)?.errorDescription ?? "Unable to load workout history."
    }
}
