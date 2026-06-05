import Combine
import Foundation

struct AIChatMessage: Identifiable, Hashable {
    let id: String
    let role: String
    let message: String
    let suggestedAction: AIChatSuggestedAction?
    let createdAt: String?
    let isPending: Bool

    var isUser: Bool {
        role == "user"
    }
}

@MainActor
final class AIChatViewModel: ObservableObject {
    @Published var messages: [AIChatMessage] = []
    @Published var draftMessage = ""
    @Published var isLoadingHistory = false
    @Published var isSending = false
    @Published var errorMessage: String?

    private let workout: WorkoutPlanResponse
    private let selectedExercise: WorkoutExerciseResponse?
    private let repository: AIChatRepositoryProtocol

    init(
        workout: WorkoutPlanResponse,
        selectedExercise: WorkoutExerciseResponse?,
        repository: AIChatRepositoryProtocol
    ) {
        self.workout = workout
        self.selectedExercise = selectedExercise
        self.repository = repository
    }

    var title: String {
        selectedExercise?.name ?? workout.title
    }

    var subtitle: String {
        if let selectedExercise {
            return "Ask about sets, form, substitutions, or intensity for \(selectedExercise.name)."
        }
        return "Ask for coaching adjustments for this workout."
    }

    func loadHistory() async {
        guard messages.isEmpty, !isLoadingHistory else { return }
        isLoadingHistory = true
        errorMessage = nil
        defer { isLoadingHistory = false }

        do {
            let response = try await repository.getHistory(workoutId: workout.workoutID, limit: 50, offset: 0)
            messages = response.items.map {
                AIChatMessage(
                    id: $0.id,
                    role: $0.role,
                    message: $0.message,
                    suggestedAction: $0.suggestedAction,
                    createdAt: $0.createdAt,
                    isPending: false
                )
            }
        } catch {
            errorMessage = readableMessage(for: error, fallback: "Unable to load coach history.")
        }
    }

    func sendMessage() async {
        let trimmedMessage = draftMessage.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedMessage.isEmpty, !isSending else { return }

        let userMessage = AIChatMessage(
            id: "local-user-\(UUID().uuidString)",
            role: "user",
            message: trimmedMessage,
            suggestedAction: nil,
            createdAt: nil,
            isPending: true
        )
        messages.append(userMessage)
        draftMessage = ""
        isSending = true
        errorMessage = nil
        defer { isSending = false }

        do {
            let response = try await repository.sendMessage(
                AIChatRequest(
                    workoutId: workout.workoutID,
                    currentWorkoutPlanExerciseId: selectedExercise?.workoutPlanExerciseID,
                    message: trimmedMessage
                )
            )
            messages.append(
                AIChatMessage(
                    id: "local-assistant-\(UUID().uuidString)",
                    role: "assistant",
                    message: response.reply,
                    suggestedAction: response.suggestedAction,
                    createdAt: nil,
                    isPending: false
                )
            )
        } catch {
            messages.removeAll { $0.id == userMessage.id }
            draftMessage = trimmedMessage
            errorMessage = readableMessage(for: error, fallback: "Unable to send message.")
        }
    }

    private func readableMessage(for error: Error, fallback: String) -> String {
        if let apiError = error as? APIError {
            switch apiError {
            case .server(let code, let message):
                if code == "AI_LIMIT_REACHED" {
                    return "AI chat limit reached for today."
                }
                return message
            case .transport:
                return "Network error. Please try again."
            case .decodingError:
                return "Received an unexpected response from the server."
            case .unauthorized:
                return "Your session expired. Please log in again."
            default:
                return fallback
            }
        }
        return (error as? LocalizedError)?.errorDescription ?? fallback
    }
}
