import Foundation

struct CalculateReadinessRequest: Codable {
    let date: String
}

struct ReadinessFactor: Codable, Equatable {
    let score: Double?
    let impact: String?
    let message: String?
}

struct ReadinessResponse: Codable, Equatable {
    let id: String?
    let date: String
    let score: Double
    let category: String
    let recommendation: String
    let confidence: Double
    let explanation: String
    let factorBreakdown: [String: ReadinessFactor]?

    enum CodingKeys: String, CodingKey {
        case id
        case date
        case score
        case category
        case recommendation
        case confidence
        case explanation
        case factorBreakdown = "factor_breakdown"
    }

    var displayScore: Int {
        Int(score.rounded())
    }
}

struct ReadinessHistoryItem: Codable, Equatable, Identifiable {
    let id: String
    let date: String
    let score: Double
    let category: String
    let recommendation: String
    let confidence: Double
    let explanation: String

    init(from readiness: ReadinessResponse) {
        self.id = readiness.id ?? readiness.date
        self.date = readiness.date
        self.score = readiness.score
        self.category = readiness.category
        self.recommendation = readiness.recommendation
        self.confidence = readiness.confidence
        self.explanation = readiness.explanation
    }
}

extension ReadinessResponse {
    static let mockExcellent = ReadinessResponse(
        id: "excellent",
        date: "2026-06-01",
        score: 86,
        category: "excellent",
        recommendation: "train_hard",
        confidence: 0.88,
        explanation: "Your recovery markers look strong enough for a productive training day.",
        factorBreakdown: nil
    )

    static let mockLow = ReadinessResponse(
        id: "low",
        date: "2026-06-01",
        score: 34,
        category: "low",
        recommendation: "recovery",
        confidence: 0.62,
        explanation: "Recovery looks suppressed today. Reduce intensity or keep the session restorative.",
        factorBreakdown: nil
    )
}
