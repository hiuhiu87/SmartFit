import Foundation

actor LocalWorkoutStore {
    private var cachedWorkoutIDs: [UUID] = []

    func save(workoutID: UUID) {
        guard !cachedWorkoutIDs.contains(workoutID) else { return }
        cachedWorkoutIDs.append(workoutID)
    }

    func allWorkoutIDs() -> [UUID] {
        cachedWorkoutIDs
    }

    func clear() {
        cachedWorkoutIDs.removeAll()
    }
}
